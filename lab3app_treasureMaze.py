'''Streamlit web app for the Treasure Maze.

How Streamlit works: after EVERY click the whole script runs again from the top.
So everything that must survive a click (the environment, the Agent, the visited path, the log)
is kept in st.session_state. The buttons call a function (on_click) that changes it,
then the page is drawn again with the new state.

Run it with:  python -m streamlit run lab3app_treasureMaze.py
'''

# Import dependencies
import random

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # to display the HTML code

from pyvis.network import Network  # to create the graph as an interactive html object

from data.treasureMazeData import mazeData, mazeLocations, mazeStart, mazeFinish, treasureTypes, exitIcon
from src.mazeGraphClass import MazeGraph
from src.treasureClass import Treasure
from src.treasureMazeEnvironmentClass import TreasureMazeEnvironment
from src.mazeProblemSolvingAgentClass import versions
from src.agents import ProblemSolvingMazeAgentBFS


goalDescriptions = {
    'Basic': "Reach the finish",
    'Specific treasure': "Find a particular treasure and then reach the finish",
    'Treasure collection': "Collect ALL treasures and reach the finish",
}
arrows = {'N': '⬆️', 'E': '➡️', 'S': '⬇️', 'W': '⬅️'}
nodeColors = {
    "default": "white",
    "start": "#4caf50",
    "finish": "#e53935",
    "treasure": "gold",
    "visited": "orange",
    "agent": "deepskyblue",
    "goal": "#ff4fd8",
}

# distance in pixels between two columns / two rows of the maze picture
CELL_WIDTH = 115
CELL_HEIGHT = 135


def treasureLabel(name):
    '''Example: 'Gold' -> '🪙 Pile of Gold' '''
    icon, description = treasureTypes[name]
    return f"{icon} {description}"


# ---------------------------------------------------------------------------
# Creating the game
# ---------------------------------------------------------------------------

def newPlacement():
    '''Random treasure placement (the environment follows the rules of the task).
    Returns {node: treasure name}.'''
    mazeGraph = MazeGraph(mazeData, mazeLocations)
    env = TreasureMazeEnvironment(mazeGraph, mazeStart, mazeFinish, list(treasureTypes))
    return env.treasures_map()


def startGame():
    '''A new environment with the current treasures + a new Agent for the chosen version.'''
    mazeGraph = MazeGraph(mazeData, mazeLocations)
    env = TreasureMazeEnvironment(mazeGraph, mazeStart, mazeFinish)
    for node, name in st.session_state["placement"].items():
        env.add_thing(Treasure(name), node)

    version = st.session_state["version"]
    target = st.session_state.get("target")
    if target == "nearest":
        target = None  # None = the nearest treasure

    agent = ProblemSolvingMazeAgentBFS(mazeStart, mazeGraph, mazeFinish, version, target)
    env.add_thing(agent)  # the Agent formulates its goal and searches for a solution

    st.session_state["env"] = env
    st.session_state["agent"] = agent
    st.session_state["visited"] = [agent.state]  # the nodes the Agent has walked through
    st.session_state["log"] = []                 # one row per executed action
    st.session_state["lastGoal"] = describeGoal(agent)


def shuffleTreasures():
    st.session_state["placement"] = newPlacement()
    startGame()


# ---------------------------------------------------------------------------
# Running the Agent (button callbacks)
# ---------------------------------------------------------------------------

def AgentStep():
    '''One step of the environment + one row in the log.'''
    env = st.session_state["env"]
    agent = st.session_state["agent"]
    if not env.is_agent_alive(agent):
        return

    bagBefore = len(agent.bag)
    actions = env.step()
    action = None
    if actions:
        action = actions[0]

    # what happened in this step?
    events = []
    if len(agent.bag) > bagBefore:
        events.append(f"grabbed {treasureLabel(agent.bag[-1])}")

    goal = describeGoal(agent)
    if goal != st.session_state["lastGoal"] and not agent.escaped:
        events.append(f"new goal: {goal}")
        st.session_state["lastGoal"] = goal

    if agent.escaped:
        events.append(f"found the exit {exitIcon}")
        st.session_state["celebrate"] = True  # show the balloons once
    elif not agent.alive:
        events.append(f"dead (performance {agent.performance})")

    # remember the path and the log
    if agent.state != st.session_state["visited"][-1]:  # a turn doesn't change the node
        st.session_state["visited"].append(agent.state)
    st.session_state["log"].append({
        "Step": len(st.session_state["log"]) + 1,
        "Action": action,
        "Position": agent.state,
        "Heading": f"{arrows[agent.heading]} {agent.heading}",
        "Performance": agent.performance,
        "Event": "; ".join(events),
    })


def AgentRun():
    '''Steps until the Agent escapes or dies.'''
    while st.session_state["env"].is_agent_alive(st.session_state["agent"]):
        AgentStep()


def describeGoal(agent):
    '''The current goal of the Agent as a text.'''
    if agent.goal is None:
        return "-"
    if agent.goal == agent.exit:
        return f"{exitIcon} Exit ({agent.exit})"
    if isinstance(agent.goal, list):
        return f"the nearest treasure ({', '.join(agent.goal)})"
    return f"{treasureLabel(agent.target)} at {agent.goal}"


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def nodeLook(node, treasures, agent, visited):
    '''Label, color and size of a node. The rules are checked in order: a later rule wins.'''
    label = node
    color = nodeColors["default"]
    size = 16

    if node in visited:
        color = nodeColors["visited"]
    if node == mazeStart:
        color = nodeColors["start"]
    if node == mazeFinish:
        color = nodeColors["finish"]
        label = f"{node} {exitIcon}"
    if node in treasures:
        color = nodeColors["treasure"]
        icon = treasureTypes[treasures[node]][0]
        label = f"{node} {icon}"
    if node == agent.state:
        color = nodeColors["agent"]
        label = f"🤖{arrows[agent.heading]} {node}"
        size = 26

    return label, color, size


def buildGraph(env, agent, visited):
    # no font_color here: pyvis would replace the font (size) of every node with it
    net = Network(bgcolor="#242020", height="640px", width="100%", cdn_resources="remote")

    if isinstance(agent.goal, list):
        goals = agent.goal
    else:
        goals = [agent.goal]

    # nodes: placed exactly like in the maze picture
    treasures = env.treasures_map()
    for node in env.status.nodes():
        x, y = env.status.getLocation(node)
        label, color, size = nodeLook(node, treasures, agent, visited)

        if node in goals and agent.alive:  # the current goal gets a thick pink border
            border = nodeColors["goal"]
            borderWidth = 6
        else:
            border = color
            borderWidth = 1

        net.add_node(node, label=label, title=node, x=x * CELL_WIDTH, y=y * CELL_HEIGHT, size=size, physics=False,
                     color={"background": color, "border": border}, borderWidth=borderWidth,
                     font={"size": 26, "color": "white"})

    # edges: the corridors the Agent has walked are orange
    walked = list(zip(visited, visited[1:]))  # pairs of consecutive visited nodes
    for node_source in env.status.nodes():
        for node_target in env.status.get(node_source):
            if node_source < node_target:  # every corridor is stored in both directions: draw it once
                if (node_source, node_target) in walked or (node_target, node_source) in walked:
                    net.add_edge(node_source, node_target, color="orange", width=4)
                else:
                    net.add_edge(node_source, node_target, color="#9e9e9e", width=2)

    net.toggle_physics(False)

    # show the graph (with a dark background around it)
    html = net.generate_html()
    html = html.replace("</head>", "<style>body{margin:0;background:#242020} .card{border:none}</style></head>")
    if hasattr(st, "iframe"):  # new Streamlit versions replace components.html with st.iframe
        st.iframe(html, height=645)
    else:
        components.html(html, height=645)


def legendItem(text, color):
    '''A colored dot + a text, in HTML.'''
    dot = ("<span style='display:inline-block;width:12px;height:12px;border-radius:50%;"
           f"background:{color};border:1px solid #888;vertical-align:middle'></span>")
    return f"<span style='display:inline-block;margin:2px 10px 2px 0'>{dot} {text}</span>"


def showLegend():
    legend = [
        ("Start", nodeColors["start"]),
        ("Finish " + exitIcon, nodeColors["finish"]),
        ("Treasure", nodeColors["treasure"]),
        ("Visited", nodeColors["visited"]),
        ("Agent 🤖", nodeColors["agent"]),
        ("Current goal (border)", nodeColors["goal"]),
    ]
    items = []
    for text, color in legend:
        items.append(legendItem(text, color))
    st.markdown(" ".join(items), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Page parts
# ---------------------------------------------------------------------------

def targetText(option):
    '''How an option of the "Treasure to find" box is shown.'''
    if option == "nearest":
        return "Any (the nearest one)"
    return treasureLabel(option)


def sidebar():
    st.sidebar.header("Maze settings")

    captions = [goalDescriptions[v] for v in versions]
    st.sidebar.radio("Version (goal state)", versions, key="version", on_change=startGame, captions=captions)

    if st.session_state["version"] == "Specific treasure":
        options = ["nearest"] + list(treasureTypes)
        st.sidebar.selectbox("Treasure to find", options, key="target", on_change=startGame, format_func=targetText)

    st.sidebar.button("🎲 New maze (re-place treasures)", on_click=shuffleTreasures)
    st.sidebar.button("↺ Restart the Agent", on_click=startGame)

    # the list of treasures, in the alphabetical order of their names
    st.sidebar.subheader("Treasures in the maze")
    agent = st.session_state["agent"]
    nodeOfTreasure = {name: node for node, name in st.session_state["placement"].items()}
    for name in sorted(nodeOfTreasure):
        status = ""
        if name in agent.bag:
            status = " ✅ grabbed"
        st.sidebar.write(f"{treasureLabel(name)} at **{nodeOfTreasure[name]}**{status}")


def showAgentPanel(agent):
    st.subheader("The Agent", divider="red")
    c1, c2, c3 = st.columns(3)
    c1.metric("Position", agent.state)
    c2.metric("Heading", f"{arrows[agent.heading]} {agent.heading}")
    c3.metric("Performance", agent.performance)

    st.info(f"The Agent goal is: {describeGoal(agent)}")
    if agent.bag:
        bag = ", ".join(treasureLabel(t) for t in agent.bag)
    else:
        bag = "empty"
    st.info(f"Treasures grabbed: {bag}")

    if agent.escaped:
        st.success(f"{exitIcon} The Agent found the exit with performance {agent.performance}.")
        if st.session_state.pop("celebrate", False):
            st.balloons()
        return

    if not agent.alive:
        st.error(f"Agent in location {agent.state} and it is dead (performance {agent.performance}).")
        return

    # the Agent is still working
    if agent.seq:
        st.write(f"**Planned actions ({len(agent.seq)}):** {' → '.join(agent.seq)}")
        if len(agent.seq) > agent.performance:
            st.warning(f"The plan needs {len(agent.seq)} more actions, but the Agent's performance is only "
                       f"{agent.performance}: it will die on the way.")
    b1, b2 = st.columns(2)
    b1.button("Run One Agent's Step", on_click=AgentStep, type="primary")
    b2.button("Run to the end", on_click=AgentRun)


def showLog():
    if st.session_state["log"]:
        st.subheader("Executed actions", divider="gray")
        st.dataframe(pd.DataFrame(st.session_state["log"]), hide_index=True)


def showExplanation(env):
    nodesCount = len(env.status.nodes())
    with st.expander("How the Agent solves the maze"):
        st.markdown(f"""
* **State space:** a node for the start **S**, the finish **F** {exitIcon}, the dead end **F2** and every junction / turning point;
  the edges are corridors of the maze (cost 1). The second copies of the repeated labels in the task picture are named E2, F2, J2, L2.
* **State** = (position, heading, treasures collected). **Actions:** `advance` (go along the corridor in front),
  `left` / `right` (turn 90°). Turning around at a dead end = two turns.
* **Performance:** initially 50% of the number of nodes ({nodesCount} // 2 = {nodesCount // 2}); every executed action costs 1.
  The Agent dies when its performance reaches 0.
* **Treasures:** placed randomly - never at S or F, one treasure per node. The Agent grabs a treasure when it steps on its node.
* **Specific treasure:** goal = the treasure's node; after the grab the Agent **re-defines its goal** to the exit and searches again.
* **Treasure collection:** one search with goal = (F, {{Gold, Diamond, Pizza, ExtraPoints}}): the Agent cannot stop at F before it has all 4 treasures.
* **Search:** Breadth-First Search (uninformed, FIFO frontier) - every action costs 1, so the plan has the fewest actions.
""")


def main():
    st.set_page_config(page_title="Treasure Maze", page_icon="🪙", layout="wide")

    # first visit: a random maze, the version 'Specific treasure' with the nearest treasure
    if "placement" not in st.session_state:
        st.session_state["placement"] = newPlacement()
        st.session_state["version"] = "Specific treasure"
        st.session_state["target"] = "nearest"
    if "agent" not in st.session_state:
        startGame()

    sidebar()
    env = st.session_state["env"]
    agent = st.session_state["agent"]

    # Set header title
    st.header("Problem Solving Agents: Treasure Maze")
    st.caption(f"Version: **{agent.version}** - {goalDescriptions[agent.version]}. "
               "Breadth-First Search over the state (position, heading, treasures collected); "
               "actions: advance, left, right.")

    graphCol, infoCol = st.columns([3, 2])
    with graphCol:
        st.subheader("State of the Environment", divider="red")
        buildGraph(env, agent, st.session_state["visited"])
        showLegend()
    with infoCol:
        showAgentPanel(agent)

    showLog()
    showExplanation(env)


if __name__ == '__main__':
    main()
