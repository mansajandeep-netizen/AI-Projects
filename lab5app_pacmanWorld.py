'''Streamlit web app for Lab 5: Pac-Man in the PacMan World - informed search with A*, IDA* and RBFS.

How Streamlit works: after EVERY click the whole script runs again from the top.
So everything that must survive a click (the three worlds with their Pac-Men, the log)
is kept in st.session_state. The buttons call a function (on_click) that changes it,
then the page is drawn again with the new state.

Run it with:  python -m streamlit run lab5app_pacmanWorld.py
'''

# Import dependencies
import io
import random
import time
from contextlib import redirect_stdout

import matplotlib
matplotlib.use("Agg")  # draw pictures without opening a window
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # to display the HTML code (older Streamlit versions)

from src.pacmanData import (makePacmanMaze, buildPacmanGraph, drawPacmanWorld, pacmanPyvis,
                            exactCostsFrom, bestFoodOrder, SEGMENT_COLORS, WALL)
from src.pacmanEnvironmentClass import PacmanWorldEnvironment
from src.pacmanThings import Food, Ghost
from src.agents import PacmanAgentAstar, PacmanAgentIDAstar, PacmanAgentRBFS
from src.PS_agentPrograms import A_StarSearchAgentProgram
from src.mazeProblemClass import MazeProblem
from src.heuristics import mazeCostHeuristic, manhattanDistance, euclideanDistance

DEMO_SEED = 67          # the world of the notebook
N = 10                  # 10 x 10 maze
SPACE = N * N           # "space cells" -> start performance 40%, ghost power 20%-30%
MAX_EXPANSIONS = 200_000  # IDA* / RBFS give up after this many expanded nodes (keeps the page fast)

heuristics = {
    'maze-cost (Task 4, never overestimates)': mazeCostHeuristic,
    'Manhattan (Task 2)': manhattanDistance,
    'Euclidean (tutorial)': euclideanDistance,
}
pacmen = [('A*', PacmanAgentAstar), ('IDA*', PacmanAgentIDAstar), ('RBFS', PacmanAgentRBFS)]
pacColors = SEGMENT_COLORS[:3]  # A* blue, IDA* orange, RBFS green
arrows = {'left': '⬅️', 'up': '⬆️', 'right': '➡️', 'down': '⬇️'}
cellColors = {'free': '#eef3fb', 'wall': '#4b4f56', 'start': '#d6ecff', 'exit': '#c8ebc8'}


# ---------------------------------------------------------------------------
# Creating the world (one copy per Pac-Man, so each one eats its own food)
# ---------------------------------------------------------------------------

def startWorld():
    '''The world of the current seed + three Pac-Men at the start. A Pac-Man plans its route when it is added.'''
    seed = st.session_state["seed"]
    maze, start, exit_, foods = makePacmanMaze(N, seed=seed)
    graph = buildPacmanGraph(maze)
    h = heuristics[st.session_state["heuristic"]]
    rational = st.session_state["order"] == "rational"

    worlds, agents, planTimes = {}, {}, {}
    for name, factory in pacmen:
        env = PacmanWorldEnvironment(maze, start, exit_, seed=seed, verbose=False)  # same seed = same ghosts
        limit = {} if name == 'A*' else {'max_expansions': MAX_EXPANSIONS}
        agent = factory(start, graph, foods, exit_, SPACE, h=h, rational=rational,
                        name=f'Pac-Man ({name})', verbose=False, **limit)
        agent.performance = st.session_state["startPerformance"]
        t0 = time.perf_counter()
        with redirect_stdout(io.StringIO()):
            env.add_thing(agent)  # the agent formulates its goals and searches its route here
        planTimes[name] = time.perf_counter() - t0
        worlds[name], agents[name] = env, agent

    st.session_state.update(maze=maze, start=start, exit=exit_, foods=foods, graph=graph,
                            worlds=worlds, agents=agents, planTimes=planTimes,
                            ghosts=dict(worlds['A*'].ghosts), step=0, log=[])


def randomWorld():
    st.session_state["seed"] = random.randint(0, 99999)
    startWorld()


# ---------------------------------------------------------------------------
# Running the Pac-Men (button callbacks)
# ---------------------------------------------------------------------------

def eventText(event):
    time_, kind, cell, perf = event
    if kind == 'food':
        return f"🍒 ate food → ×2 = {perf:g}"
    if kind == 'won':
        return f"👻 beat a ghost (power {st.session_state['ghosts'].get(cell)}) → −10% = {perf:g}"
    if kind == 'killed':
        return f"💀 killed by a ghost (power {st.session_state['ghosts'].get(cell)})"
    if kind == 'dead':
        return "🪫 out of performance"
    if kind == 'exit':
        return "🚪 reached the exit"
    return kind


def pacmenStep():
    '''One step: every Pac-Man that is still on the way makes one move in its own world.'''
    step = st.session_state["step"] + 1
    moved = False
    for name, env in st.session_state["worlds"].items():
        agent = st.session_state["agents"][name]
        if env.is_done():
            continue
        action = agent.seq[0]
        before = len(agent.events)
        with redirect_stdout(io.StringIO()):
            env.step()
        moved = True
        st.session_state["log"].append({
            "Step": step,
            "Pac-Man": name,
            "Action": f"{arrows[action]} {action}",
            "Position": str(agent.state),
            "Performance": agent.performance,
            "Event": "; ".join(eventText(e) for e in agent.events[before:]),
        })
    if moved:
        st.session_state["step"] = step


def pacmenRun():
    '''Steps until every Pac-Man has reached the exit, been killed or has no route.'''
    for _ in range(1000):
        if all(env.is_done() for env in st.session_state["worlds"].values()):
            break
        pacmenStep()


def status(agent):
    if agent.gave_up:
        return '⛔ gave up planning'
    if not agent.alive:
        return '💀 killed by a ghost' if any(e[1] == 'killed' for e in agent.events) else '🪫 out of performance'
    if agent.done:
        return '🚪 reached the exit'
    if not agent.seq:
        return '⛔ no route'
    return '🟡 on the way'


def allDone():
    return all(env.is_done() for env in st.session_state["worlds"].values())


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def badge(name, k, agent):
    mark = '' if agent.alive and not agent.gave_up else ' ✖'
    return f"<span class='badge' style='background:{pacColors[k]}'>{name}{mark}</span>"


def worldGridHtml(viewName, showGhosts):
    '''The maze as a grid, as the selected Pac-Man's world looks right now.
    ● = a cell this Pac-Man has walked through, ○ = a cell of its route it hasn't reached yet.'''
    maze = st.session_state["maze"]
    start, exit_ = st.session_state["start"], st.session_state["exit"]
    env = st.session_state["worlds"][viewName]
    agent = st.session_state["agents"][viewName]
    k = [name for name, _ in pacmen].index(viewName)

    foodLeft = {t.location for t in env.things if isinstance(t, Food)}
    ghostsLeft = {t.location: t.power for t in env.things if isinstance(t, Ghost)}
    ghostsBeaten = {e[2] for e in agent.events if e[1] == 'won'}
    walked = {h[1] for h in agent.history}
    planned = {c for seg in agent.segments for c in seg['path']}

    html = [f"<div class='maze' style='grid-template-columns: 22px repeat({N}, minmax(0, 1fr))'>", "<div></div>"]
    html += [f"<div class='head'>{j}</div>" for j in range(N)]
    for i in range(N):
        html.append(f"<div class='head'>{i}</div>")
        for j in range(N):
            cell = (i, j)
            color = cellColors['wall'] if maze[cell] == WALL else cellColors['free']
            if cell == start:
                color = cellColors['start']
            if cell == exit_:
                color = cellColors['exit']
            icons, note = [], ''
            if maze[cell] == WALL:
                icons.append('🧱')
            if cell == exit_:
                icons.append('🚪')
            if cell in foodLeft:
                icons.append('🍒')
            if cell in ghostsLeft and (showGhosts or cell in {e[2] for e in agent.events}):
                icons.append('👻')
                note = f"power {ghostsLeft[cell]}"
            elif cell in ghostsBeaten:
                icons.append('💥')
                note = 'beaten'
            if cell == start and not icons:
                icons.append('🏁')
            marks = ''
            if cell in walked:
                marks = f"<span style='color:{pacColors[k]}'>●</span>"
            elif cell in planned:
                marks = f"<span style='color:{pacColors[k]}'>○</span>"
            badges = ''.join(badge(name, kk, st.session_state["agents"][name])
                             for kk, (name, _) in enumerate(pacmen)
                             if st.session_state["agents"][name].state == cell)
            html.append(f"<div class='cell' style='background:{color}' title='{cell}'>"
                        f"<div class='pacs'>{badges}</div><div class='icon'>{''.join(icons)}</div>"
                        f"<div class='note'>{note}</div><div class='marks'>{marks}</div></div>")
    html.append("</div>")
    style = """<style>
    .maze {display:grid; gap:3px; max-width:560px; margin:4px 0 8px 0}
    .maze .head {display:flex; align-items:center; justify-content:center; font-size:12px; opacity:.6}
    .maze .cell {position:relative; aspect-ratio:1; border-radius:6px; display:flex; align-items:center;
                 justify-content:center; border:1px solid rgba(11,11,11,.12)}
    .maze .icon {font-size:clamp(12px, 3vw, 24px)}
    .maze .note {position:absolute; bottom:1px; right:3px; font-size:8px; color:#52514e}
    .maze .marks {position:absolute; bottom:0px; left:3px; font-size:11px}
    .maze .pacs {position:absolute; top:2px; left:2px; right:2px; display:flex; gap:2px; flex-wrap:wrap}
    .maze .badge {color:white; font-size:9px; font-weight:700; padding:1px 3px; border-radius:4px}
    </style>"""
    return style + "".join(html)


def legendItem(text, color):
    '''A coloured square + a text, in HTML.'''
    square = ("<span style='display:inline-block;width:12px;height:12px;border-radius:3px;"
              f"background:{color};border:1px solid #888;vertical-align:middle'></span>")
    return f"<span style='display:inline-block;margin:2px 12px 2px 0'>{square} {text}</span>"


def showLegend():
    legend = [("🧱 wall", cellColors['wall']), ("🏁 start", cellColors['start']), ("🚪 exit", cellColors['exit']),
              ("🍒 food dot", cellColors['free']), ("👻 ghost / 💥 beaten", cellColors['free'])]
    legend += [(f"Pac-Man ({name})", pacColors[k]) for k, (name, _) in enumerate(pacmen)]
    st.markdown(" ".join(legendItem(text, color) for text, color in legend) +
                "<br><small>● walked &nbsp; ○ planned (not reached yet) &nbsp; ✖ killed / no route</small>",
                unsafe_allow_html=True)


def showHtml(html, height):
    '''A pyvis page in the app (new Streamlit versions replace components.html with st.iframe)'''
    html = html.replace("</head>", "<style>body{margin:0;background:#242020} .card{border:none}</style></head>")
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        components.html(html, height=height)


def routeFigure(agent, showGhosts):
    '''Task 2 picture: every leg of the route in its own colour.'''
    fig, ax = plt.subplots(figsize=(8.5, 6.5), layout='constrained')
    ghosts = list(st.session_state["ghosts"].items()) if showGhosts else None
    drawPacmanWorld(st.session_state["maze"], st.session_state["start"], st.session_state["exit"],
                    st.session_state["foods"], ghosts=ghosts, segments=agent.segments, ax=ax,
                    food_order=agent.food_order,
                    title=f"{agent.name}: route cost {agent.total_cost}, {agent.total_steps} moves")
    st.pyplot(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Tables (cached: the same seed gives the same numbers)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def heuristicTable(seed):
    '''Task 2: start -> every food dot and the exit with each heuristic.'''
    maze, start, exit_, foods = makePacmanMaze(N, seed=seed)
    graph = buildPacmanGraph(maze)
    exact = exactCostsFrom(graph, start)
    rows = []
    for target in foods + [exit_]:
        row = {'goal': f"{'exit' if target == exit_ else 'food'} {target}", 'optimal cost': exact[target]}
        for label, h in [('Euclidean', euclideanDistance), ('Manhattan', manhattanDistance), ('maze-cost', mazeCostHeuristic)]:
            prog = A_StarSearchAgentProgram(h, verbose=False, report=False)
            prog(MazeProblem(start, target, graph))
            row[f'{label}: expanded'] = prog.stats['nodes_expanded']
            row[f'{label}: cost'] = prog.stats['path_cost']
        rows.append(row)
    table = pd.DataFrame(rows).set_index('goal')
    table.loc['TOTAL'] = table.sum()
    return table


@st.cache_data(show_spinner=False)
def foodOrderTable(seed):
    '''Task 4: listed order vs cheapest food first vs the best of all orders (A* with the maze-cost heuristic).'''
    maze, start, exit_, foods = makePacmanMaze(N, seed=seed)
    graph = buildPacmanGraph(maze)
    listed = PacmanAgentAstar(start, graph, foods, exit_, SPACE, rational=False, verbose=False)
    listed(start)
    rational = PacmanAgentAstar(start, graph, foods, exit_, SPACE, rational=True, verbose=False)
    rational(start)
    best, order = bestFoodOrder(graph, start, exit_, [f for f in foods if f not in (start, exit_)])
    table = pd.DataFrame({'route cost': [listed.total_cost, rational.total_cost, best],
                          'visiting order': [str(list(listed.food_order)), str(list(rational.food_order)), str(order)]},
                         index=['listed order (Task 2)', 'cheapest food first (Task 4)', 'best of all orders (brute force)'])
    exact = exactCostsFrom(graph, start)
    first = rational.segments[0]['goal'] if rational.segments and rational.segments[0]['kind'] == 'food' else None
    costs = {str(f): exact[f] for f in foods}
    return table, first, costs


def comparisonTable():
    '''Tasks 7-8: the three Pac-Men side by side.'''
    rows = []
    for name, _ in pacmen:
        agent = st.session_state["agents"][name]
        segs = agent.segments
        rows.append({
            'Pac-Man': name,
            'route cost': agent.total_cost if not agent.gave_up else None,
            'moves': agent.total_steps if not agent.gave_up else None,
            'nodes expanded': agent.total_expanded,
            'peak memory (nodes)': max((s['stats'].get('peak_memory', 0) for s in segs), default=None),
            'planning time (ms)': round(1000 * st.session_state["planTimes"][name], 1),
            'status': status(agent),
            'performance': agent.performance,
        })
    return pd.DataFrame(rows).set_index('Pac-Man')


# ---------------------------------------------------------------------------
# Page parts
# ---------------------------------------------------------------------------

def sidebar():
    st.sidebar.header("PacMan World")
    st.sidebar.number_input("Seed (the same seed = the same world)", min_value=0, max_value=99999, step=1,
                            key="seed", on_change=startWorld)
    st.sidebar.button("🎲 New random world", on_click=randomWorld)
    st.sidebar.button("↺ Restart the Pac-Men", on_click=startWorld)

    st.sidebar.subheader("Search")
    st.sidebar.selectbox("Heuristic h(n)", list(heuristics), key="heuristic", on_change=startWorld,
                         help="Moves cost up 2, down 1, left/right 0. Only the maze-cost heuristic never "
                              "overestimates, so only it guarantees the cheapest route.")
    st.sidebar.radio("Food order", ["rational", "listed"], key="order", on_change=startWorld,
                     format_func=lambda o: "cheapest food first (Task 4)" if o == "rational" else "listed order (Task 2)")

    st.sidebar.subheader("Pac-Man")
    st.sidebar.slider("Start performance", min_value=5, max_value=80, step=1, key="startPerformance",
                      on_change=startWorld,
                      help=f"Task 5: 40% of the {SPACE} cells = 40. Lower it to see a weak Pac-Man lose a fight.")
    st.sidebar.toggle("Show the ghosts", key="showGhosts",
                      help="Pac-Man doesn't know where the ghosts are: it only notices a ghost in its own cell.")

    st.sidebar.subheader("Ghosts")
    st.sidebar.caption(f"Power: random, 20%-30% of the {SPACE} cells = {int(0.2 * SPACE)}-{int(0.3 * SPACE)}")
    for cell, power in st.session_state["ghosts"].items():
        st.sidebar.write(f"👻 {cell}: power **{power}**")


def pacmanPanel(name, k):
    agent = st.session_state["agents"][name]
    st.markdown(f"<span style='color:{pacColors[k]};font-size:20px'>■</span> **Pac-Man ({name})**",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Performance", f"{agent.performance:g}")
    c2.metric("Position", str(agent.state))
    st.write(f"**{status(agent)}**")
    if agent.gave_up:
        st.caption(f"{name} stopped after {MAX_EXPANSIONS:,} expanded nodes. It does not remember visited cells, "
                   f"and the free left/right moves give it a huge number of equally cheap paths to try.")
    elif agent.segments:
        st.caption(f"Route: cost {agent.total_cost}, {agent.total_steps} moves, "
                   f"{agent.total_expanded} nodes expanded, planned in {1000 * st.session_state['planTimes'][name]:.1f} ms")
    if agent.alive and agent.seq:
        nxt = " ".join(arrows[a] for a in agent.seq[:16])
        st.caption("Next moves: " + nxt + (" …" if len(agent.seq) > 16 else ""))


def showResult():
    if not allDone():
        return
    finished = {name: a for name, a in st.session_state["agents"].items() if a.done and a.alive}
    if not finished:
        st.warning("No Pac-Man reached the exit.")
        return
    best = max(a.performance for a in finished.values())
    winners = [name for name, a in finished.items() if a.performance == best]
    st.success(f"🏆 Highest performance at the exit: **{' = '.join(winners)}** with {best:g}.")


def showTabs():
    agents = st.session_state["agents"]
    view = st.session_state["view"]
    tabRoute, tabCompare, tabHeur, tabOrder, tabGraph, tabLog, tabPerf = st.tabs(
        ["Route (legs in colours)", "A* vs IDA* vs RBFS", "Heuristics", "Food order", "Interactive graph", "Log", "Performance"])
    with tabRoute:
        st.caption("Task 2: each leg of the route has its own colour (start → food 1, food 1 → food 2, …, → exit). "
                   "The small number next to a food dot is the order in which it is eaten.")
        if agents[view].segments:
            routeFigure(agents[view], st.session_state["showGhosts"])
        else:
            st.info(f"{view} has no route in this world.")
    with tabCompare:
        st.caption("Tasks 7-8: the same Pac-Man agent with three search programs, in three copies of the same world.")
        st.dataframe(comparisonTable())
        st.markdown("* With the maze-cost heuristic all three find a route with the same cost.\n"
                    "* IDA\\* and RBFS store only the current path, but they repeat work: they expand more nodes.\n"
                    "* Their routes can have more moves: free sideways moves don't change the cost, "
                    "but every move costs Pac-Man 1 performance point. A\\* prefers fewer moves on a tie.")
    with tabHeur:
        st.caption("Task 2: A* from the start to every food dot and to the exit. 'optimal cost' = the true cheapest cost.")
        st.dataframe(heuristicTable(st.session_state["seed"]))
        st.markdown("Manhattan usually expands the fewest nodes, but Euclidean and Manhattan can **overestimate** "
                    "(left/right moves are free), so they don't guarantee the cheapest path. "
                    "The maze-cost heuristic counts only the unavoidable vertical moves (2 per row up, 1 per row down).")
    with tabOrder:
        table, first, costs = foodOrderTable(st.session_state["seed"])
        st.caption("Task 4: with the whole list of remaining food dots as the goal, A* stops at the cheapest one.")
        st.dataframe(table)
        st.write(f"True cost from the start to each food dot: {costs}")
        if first is not None:
            st.write(f"First food chosen by the rational Pac-Man: **{first}** (cost {costs[str(first)]}); "
                     f"the cheapest possible is {min(costs.values())}.")
    with tabGraph:
        st.caption(f"The state space as a pyvis network (like the tutorial). Thick coloured edges: the route of {view}, "
                   "one colour per leg. Yellow = food, gold = start, green = exit, red = wall.")
        html = pacmanPyvis(st.session_state["graph"], st.session_state["maze"], st.session_state["start"],
                           st.session_state["exit"], agents[view].segments, filename=None, heading='',
                           cdn_resources='remote', height='620px')
        showHtml(html, 660)
    with tabLog:
        if st.session_state["log"]:
            st.dataframe(pd.DataFrame(st.session_state["log"]), hide_index=True)
        else:
            st.caption("No moves yet. Press Step or Run to the end.")
    with tabPerf:
        data = {f"Pac-Man ({name})": pd.Series({h[0]: h[2] for h in a.history}) for name, a in agents.items()}
        perf = pd.DataFrame(data)
        perf.index.name = "Step"
        st.caption("Every move −1, every food dot ×2, every beaten ghost −10%. "
                   "IDA* and RBFS often make identical runs, so one line can hide the other.")
        st.line_chart(perf, color=pacColors, x_label="step (moves made)", y_label="performance")
        st.dataframe(perf)


def showExplanation():
    with st.expander("How it works"):
        st.markdown(f"""
* **World:** a random {N}×{N} maze – 20% walls, **5% food dots** (5), the start and the exit (they may also have food).
  Only worlds where every food dot and the exit can be reached are used.
* **Step costs:** up 2, down 1, left 0, right 0. Sideways moves are free, so straight-line distances can overestimate.
* **Goals:** all food dots, then the exit. **Rational order:** A\\* gets the list of the remaining food dots as its goal
  and stops at the first one it reaches – with the maze-cost heuristic (2 per row up, 1 per row down) that is the
  cheapest food dot to reach.
* **Performance:** starts at 40% of the {SPACE} cells = 40; every move −1; a food dot doubles it.
* **Ghosts:** 5, hidden, never on the start, the exit, a food dot or another ghost; power 20%-30% of the cells.
  Pac-Man fights a ghost it walks into: it wins if performance > power (then −10%), otherwise it is killed.
* **A\\*** keeps every reached cell in memory. **IDA\\*** repeats depth-first searches with a growing f-limit.
  **RBFS** follows the best path and backs up when its f-value grows above the best alternative.
  IDA\\* and RBFS store only the current path; in the app they give up after {MAX_EXPANSIONS:,} expanded nodes.
""")


def main():
    st.set_page_config(page_title="PacMan World", page_icon="🟡", layout="wide")

    # first visit: the world of the notebook
    if "seed" not in st.session_state:
        st.session_state["seed"] = DEMO_SEED
        st.session_state["heuristic"] = list(heuristics)[0]
        st.session_state["order"] = "rational"
        st.session_state["startPerformance"] = round(0.4 * SPACE)
        st.session_state["showGhosts"] = True
        st.session_state["view"] = "A*"
    if "worlds" not in st.session_state:
        with st.spinner("Pac-Man is planning its route..."):
            startWorld()

    sidebar()

    # Set header title
    st.header("Pac-Man in the PacMan World: A* vs IDA* vs RBFS")
    st.caption(f"World seed {st.session_state['seed']} · start {st.session_state['start']} · "
               f"exit {st.session_state['exit']} · {len(st.session_state['foods'])} food dots · "
               f"step {st.session_state['step']}")

    worldCol, pacCol = st.columns([3, 2])
    with worldCol:
        st.subheader("The world", divider="gray")
        st.radio("Show the world of", [name for name, _ in pacmen], key="view", horizontal=True,
                 format_func=lambda n: f"Pac-Man ({n})")
        st.html(worldGridHtml(st.session_state["view"], st.session_state["showGhosts"]))
        showLegend()
    with pacCol:
        st.subheader("The Pac-Men", divider="gray")
        b1, b2 = st.columns(2)
        b1.button("Step", on_click=pacmenStep, type="primary", disabled=allDone(), width="stretch")
        b2.button("Run to the end", on_click=pacmenRun, disabled=allDone(), width="stretch")
        showResult()
        for k, (name, _) in enumerate(pacmen):
            with st.container(border=True):
                pacmanPanel(name, k)

    showTabs()
    showExplanation()


if __name__ == '__main__':
    main()
