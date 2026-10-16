'''Streamlit web app for Lab 4: two Rescue Robots (UCS and IDDFS) in a Hazardous Laboratory Maze.

How Streamlit works: after EVERY click the whole script runs again from the top.
So everything that must survive a click (the environment with the robots, the log, the energy history)
is kept in st.session_state. The buttons call a function (on_click) that changes it,
then the page is drawn again with the new state.

Run it with:  python -m streamlit run lab4app_rescueRobots.py
'''

# Import dependencies
import io
import random
from contextlib import redirect_stdout

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # to display the HTML code

from src.labMazeData import FREE, WALL, DRONE, TARGET, START, actionCosts, actionName
from src.labMazeVisual import robotColors, cellNetwork, stateSpaceNetwork, networkHtml
from src.rescueMission import makeLaboratory
from src.agents import RescueRobotAgentUCS, RescueRobotAgentIDS

DEMO_SEED = 205  # the laboratory of the notebook
arrows = {0: '⬅️', 1: '⬆️', 2: '➡️', 3: '⬇️'}
cellColors = {
    FREE: '#eef3fb',
    WALL: '#4b4f56',
    DRONE: '#f4a3a3',
    TARGET: '#ffd966',
    START: '#9fd79f',
}
statusIcons = {
    'on the way': '🚶',
    'target reached': '🌍',
    'captured by a drone': '🛸',
    'battery exhausted': '🪫',
    'no solution': '⛔',
    'stopped': '🛑',
}
searchNames = {'UCS Robot': 'Uniform-Cost Search, f(n) = g(n)', 'IDDFS Robot': 'Iterative Deepening (Iterative DLS)'}


# ---------------------------------------------------------------------------
# Creating the mission
# ---------------------------------------------------------------------------

def startMission():
    '''The laboratory of the current seed + both robots at the start. The robots plan when they are added.'''
    lab, graph, env = makeLaboratory(st.session_state["seed"], solvable=not st.session_state["allowUnsolvable"])
    planning = io.StringIO()
    with redirect_stdout(planning):  # the robots print their search; keep it for the "Search" tab
        for robot in (RescueRobotAgentUCS(graph.start, graph, graph.target), RescueRobotAgentIDS(graph.start, graph, graph.target)):
            env.add_thing(robot)

    st.session_state["env"] = env
    st.session_state["graph"] = graph
    st.session_state["fullEnergy"] = len(graph.nodes())
    st.session_state["planning"] = planning.getvalue()
    st.session_state["step"] = 0
    st.session_state["log"] = []  # one row per executed move
    st.session_state["energy"] = [{"Step": 0, **{robot.name: robot.performance for robot in env.agents}}]


def randomLaboratory():
    st.session_state["seed"] = random.randint(0, 99999)
    startMission()


# ---------------------------------------------------------------------------
# Running the robots (button callbacks)
# ---------------------------------------------------------------------------

def robotsStep():
    '''One step of the environment: every robot on the way makes one move. One row per move in the log.'''
    env = st.session_state["env"]
    if env.is_done():
        return
    nextActions = {robot.name: robot.seq[0] for robot in env.agents if robot.alive and robot.seq}
    with redirect_stdout(io.StringIO()):
        env.step()
    st.session_state["step"] += 1
    step = st.session_state["step"]

    for robot in env.agents:
        if robot.name not in nextActions:
            continue
        action = nextActions[robot.name]
        drone = env.droneAt(robot.position)
        events = []
        if robot.status == 'battery exhausted':
            events.append("🪫 battery exhausted")
        elif drone is not None:
            if robot.status == 'captured by a drone':
                events.append(f"🛸 drone (attack {drone.attackPower}): captured!")
            else:
                events.append(f"🛸 drone (attack {drone.attackPower}): Defense Mode, -10% energy")
        if robot.status == 'target reached':
            events.append("🌍 target reached")
        st.session_state["log"].append({
            "Step": step,
            "Robot": robot.name,
            "Action": f"{arrows[action]} {actionName(action)}",
            "Cost": actionCosts[action],
            "Position": str(robot.position),
            "Energy": robot.performance,
            "Event": "; ".join(events),
        })
    st.session_state["energy"].append({"Step": step, **{robot.name: robot.performance for robot in env.agents}})


def robotsRun():
    '''Steps until no robot is on the way anymore.'''
    while not st.session_state["env"].is_done():
        robotsStep()


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def robotBadge(robot, k):
    return (f"<span class='badge' style='background:{robotColors[k]}'>"
            f"{robot.name.split()[0]}{'' if robot.status in ('on the way', 'target reached') else ' ✖'}</span>")


def labGridHtml(env, showDrones):
    '''The laboratory as a grid: walls 🪨, drones 🛸, the target 🌍, the robots and their paths.
    ● = a cell the robot has walked through, ○ = a cell of its plan it hasn't reached yet.'''
    lab = env.status
    n = lab.shape[0]
    knownDrones = set()
    for robot in env.agents:
        knownDrones |= set(robot.knownDrones)
    planned = [set(robot.plannedCells()) for robot in env.agents]
    walked = [set(robot.path) for robot in env.agents]

    html = ["<div class='lab' style='grid-template-columns: 22px repeat({}, minmax(0, 1fr))'>".format(n), "<div></div>"]
    html += [f"<div class='head'>{j}</div>" for j in range(n)]
    for i in range(n):
        html.append(f"<div class='head'>{i}</div>")
        for j in range(n):
            kind = int(lab[i, j])
            drone = env.droneAt((i, j))
            visible = kind != DRONE or showDrones or (i, j) in knownDrones
            color = cellColors[kind] if visible else cellColors[FREE]
            icon = {WALL: '🪨', DRONE: '🛸' if visible else '', TARGET: '🌍', START: '🏁'}.get(kind, '')
            note = f"attack {drone.attackPower}" if drone and visible else ''
            marks = ''
            for k, robot in enumerate(env.agents):
                if (i, j) in walked[k]:
                    marks += f"<span style='color:{robotColors[k]}'>●</span>"
                elif (i, j) in planned[k]:
                    marks += f"<span style='color:{robotColors[k]}'>○</span>"
            robots = ''.join(robotBadge(robot, k) for k, robot in enumerate(env.agents) if robot.position == (i, j))
            html.append(f"<div class='cell' style='background:{color}' title='{(i, j)}'>"
                        f"<div class='robots'>{robots}</div><div class='icon'>{icon}</div>"
                        f"<div class='note'>{note}</div><div class='marks'>{marks}</div></div>")
    html.append("</div>")
    style = """<style>
    .lab {display:grid; gap:3px; max-width:540px; margin:4px 0 8px 0}
    .lab .head {display:flex; align-items:center; justify-content:center; font-size:12px; opacity:.6}
    .lab .cell {position:relative; aspect-ratio:1; border-radius:6px; display:flex; align-items:center; justify-content:center;
                border:1px solid rgba(11,11,11,.12)}
    .lab .icon {font-size:clamp(14px, 4vw, 30px)}
    .lab .note {position:absolute; bottom:2px; right:4px; font-size:9px; color:#52514e}
    .lab .marks {position:absolute; bottom:1px; left:4px; font-size:11px; letter-spacing:1px}
    .lab .robots {position:absolute; top:2px; left:2px; right:2px; display:flex; gap:2px; flex-wrap:wrap}
    .lab .badge {color:white; font-size:9px; font-weight:700; padding:1px 4px; border-radius:4px}
    </style>"""
    return style + "".join(html)


def showHtml(html, height):
    '''A pyvis page in the app (new Streamlit versions replace components.html with st.iframe)'''
    html = html.replace("</head>", "<style>body{margin:0;background:#242020} .card{border:none}</style></head>")
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:
        components.html(html, height=height)


def legendItem(text, color):
    '''A colored square + a text, in HTML.'''
    square = ("<span style='display:inline-block;width:12px;height:12px;border-radius:3px;"
              f"background:{color};border:1px solid #888;vertical-align:middle'></span>")
    return f"<span style='display:inline-block;margin:2px 12px 2px 0'>{square} {text}</span>"


def showLegend():
    legend = [("free cell", cellColors[FREE]), ("🪨 wall/debris", cellColors[WALL]), ("🛸 security drone", cellColors[DRONE]),
              ("🌍 rescue target", cellColors[TARGET]), ("🏁 start", cellColors[START]),
              ("UCS Robot", robotColors[0]), ("IDDFS Robot", robotColors[1])]
    st.markdown(" ".join(legendItem(text, color) for text, color in legend) +
                "<br><small>● walked &nbsp; ○ planned (not reached yet) &nbsp; ✖ the mission failed</small>",
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page parts
# ---------------------------------------------------------------------------

def sidebar():
    st.sidebar.header("Laboratory")
    st.sidebar.number_input("Seed (the same seed = the same laboratory)", min_value=0, max_value=99999, step=1,
                            key="seed", on_change=startMission)
    st.sidebar.button("🎲 New random laboratory", on_click=randomLaboratory)
    st.sidebar.button("↺ Restart the robots", on_click=startMission)
    st.sidebar.checkbox("Allow laboratories without a solution", key="allowUnsolvable", on_change=startMission,
                        help="Then the walls may cut the target off: both robots must report that there is no solution.")
    st.sidebar.toggle("Show the drones", key="showDrones",
                      help="The robots don't know where the drones are: a drone becomes known when a robot enters its cell.")

    env = st.session_state["env"]
    st.sidebar.subheader("Security drones")
    fullEnergy = st.session_state["fullEnergy"]
    st.sidebar.caption(f"Attack power: random, 10%-40% of the {fullEnergy} nodes = {0.1 * fullEnergy:.1f} - {0.4 * fullEnergy:.1f}")
    for drone in env.things:
        st.sidebar.write(f"🛸 {drone.location}: attack **{drone.attackPower}**")


def robotPanel(robot, k):
    fullEnergy = st.session_state["fullEnergy"]
    st.markdown(f"<span style='color:{robotColors[k]};font-size:20px'>■</span> **{robot.name}** – {searchNames[robot.name]}",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Energy (performance)", robot.performance)
    c2.metric("Position", str(robot.position))
    st.progress(max(0.0, min(robot.performance / fullEnergy, 1.0)), text=f"battery {robot.performance} / {fullEnergy}")
    st.write(f"{statusIcons.get(robot.status, '')} **{robot.status}**")
    if robot.solution is not None:
        st.caption(f"Plan: {len(robot.nodePath()) - 1} corridors, {len(robot.plannedCells()) - 1} moves, path cost {robot.solution.path_cost}")
    if robot.alive and robot.seq:
        st.caption("Next moves: " + " ".join(arrows[a] for a in robot.seq))
    if robot.knownDrones:
        st.caption("Known drones: " + ", ".join(f"{cell} attack {attack}" for cell, attack in robot.knownDrones.items()))


def showWinner(env):
    if not env.is_done():
        return
    winners = env.winner()
    if not winners:
        st.warning("No winner: no robot reached the rescue target.")
    elif len(winners) > 1:
        st.info(f"A tie: both robots reached the target with energy {winners[0].performance}.")
    else:
        st.success(f"🏆 The winner is the **{winners[0].name}**: it reached the target with energy {winners[0].performance}.")


def showTabs(env, graph):
    tabGraph, tabCells, tabSearch, tabLog, tabEnergy = st.tabs(
        ["State-space graph", "Transition model (all actions)", "Search", "Log", "Energy"])
    with tabGraph:
        st.caption("Nodes: the start, the target and every decision point (3-4 directions). Edges: the corridors – "
                   "the direction taken at the node and the cost of the corridor. Thick edges: the plans – "
                   "blue UCS Robot, orange IDDFS Robot, green both.")
        paths = [(robot.corridorPath(), robotColors[k]) for k, robot in enumerate(env.agents)]
        showHtml(networkHtml(stateSpaceNetwork(graph, env.status, fileName=None, paths=paths, cdn_resources='remote')), 780)
    with tabCells:
        st.caption("Every available action of every cell is its own curved arrow (0 left, 1 up, 2 right, 3 down).")
        showHtml(networkHtml(cellNetwork(env.cellTM, env.status, fileName=None, cdn_resources='remote')), 780)
    with tabSearch:
        for robot in env.agents:
            st.markdown(f"**{robot.name}** – nodes of the plan: {robot.nodePath() or 'no solution'}")
        ids = env.agents[1]
        if getattr(ids.program, 'iterations', None):
            st.dataframe(pd.DataFrame(ids.program.iterations, columns=['depth limit', 'DLS result', 'nodes visited']), hide_index=True)
        st.code(st.session_state["planning"], language=None)
    with tabLog:
        if st.session_state["log"]:
            st.dataframe(pd.DataFrame(st.session_state["log"]), hide_index=True)
        else:
            st.caption("No moves yet.")
    with tabEnergy:
        energy = pd.DataFrame(st.session_state["energy"]).set_index("Step")
        st.line_chart(energy, color=robotColors[:len(energy.columns)], x_label="step", y_label="energy")
        st.dataframe(energy)


def showExplanation(graph):
    fullEnergy = len(graph.nodes())
    with st.expander("How it works"):
        st.markdown(f"""
* **Laboratory:** a random 7×7 NumPy matrix – 12 walls/debris (25%), 5 security drones (10%), the start and the rescue target.
* **State-space graph:** a node for the start, the target and every decision point (a cell with 3-4 directions);
  the edges are the corridors between them. This laboratory: {len(graph.cellTM)} cells → **{fullEnergy} nodes**.
* **Actions:** 0 Left (cost 2), 1 Up (cost 4), 2 Right (cost 2), 3 Down (cost 1). Walls and the boundary block a move.
* **Energy = performance:** the battery starts with {fullEnergy} units (the number of nodes); every move takes its action cost.
* **Drones are unknown** to the robots. Entering a drone's cell: attack ≥ 2 × energy → the robot is captured;
  otherwise **Defense Mode** takes 10% of the current energy.
* **UCS Robot:** Best-First Search with f(n) = g(n) = path cost → the cheapest plan.
  **IDDFS Robot:** DLS with the depth limit 0, 1, 2, … → the plan with the fewest corridors (it ignores the costs).
* **Winner:** the robot that reached the target with the highest energy.
""")


def main():
    st.set_page_config(page_title="Rescue Robots", page_icon="🤖", layout="wide")

    # first visit: the laboratory of the notebook
    if "seed" not in st.session_state:
        st.session_state["seed"] = DEMO_SEED
        st.session_state["allowUnsolvable"] = False
        st.session_state["showDrones"] = True
    if "env" not in st.session_state:
        startMission()

    sidebar()
    env = st.session_state["env"]
    graph = st.session_state["graph"]

    # Set header title
    st.header("Rescue Robots in a Hazardous Laboratory: UCS vs IDDFS")
    st.caption(f"Laboratory seed {st.session_state['seed']} · start {graph.start} · target {graph.target} · "
               f"{len(graph.nodes())} nodes in the state-space graph · step {st.session_state['step']}")

    labCol, robotsCol = st.columns([3, 2])
    with labCol:
        st.subheader("The laboratory", divider="gray")
        st.html(labGridHtml(env, st.session_state["showDrones"]))
        showLegend()
    with robotsCol:
        st.subheader("The robots", divider="gray")
        b1, b2 = st.columns(2)
        b1.button("Step", on_click=robotsStep, type="primary", disabled=env.is_done(), width="stretch")
        b2.button("Run to the end", on_click=robotsRun, disabled=env.is_done(), width="stretch")
        showWinner(env)
        for k, robot in enumerate(env.agents):
            with st.container(border=True):
                robotPanel(robot, k)

    showTabs(env, graph)
    showExplanation(graph)


if __name__ == '__main__':
    main()
