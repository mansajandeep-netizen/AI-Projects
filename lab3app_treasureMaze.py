# Import dependencies
import random

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components #to display the HTML code

from pyvis.network import Network #to create the graph as an interactive html object

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


def treasureLabel(name):
    icon, description = treasureTypes[name]
    return "{} {}".format(icon, description)


def newPlacement():
    #random treasure placement following the rules of the task (checked by the environment)
    env = TreasureMazeEnvironment(MazeGraph(mazeData, mazeLocations), mazeStart, mazeFinish, list(treasureTypes))
    return env.treasures_map()


def startGame():
    #the environment with the current treasures + a new Agent for the chosen version
    mazeGraph = MazeGraph(mazeData, mazeLocations)
    env = TreasureMazeEnvironment(mazeGraph, mazeStart, mazeFinish)
    for node, name in st.session_state["placement"].items():
        env.add_thing(Treasure(name), node)

    target = st.session_state.get("target")
    agent = ProblemSolvingMazeAgentBFS(mazeStart, mazeGraph, mazeFinish, st.session_state["version"],
                                       None if target == "nearest" else target)
    env.add_thing(agent) #the Agent formulates its goal and searches for a solution

    st.session_state["env"] = env
    st.session_state["agent"] = agent
    st.session_state["visited"] = [agent.state]
    st.session_state["log"] = []
    st.session_state["lastGoal"] = describeGoal(agent)


def shuffleTreasures():
    st.session_state["placement"] = newPlacement()
    startGame()


def AgentStep():
    e, a = st.session_state["env"], st.session_state["agent"]
    if not e.is_agent_alive(a):
        return
    bagBefore = len(a.bag)
    actions = e.step()
    action = actions[0] if actions else None

    events = []
    if len(a.bag) > bagBefore:
        events.append("grabbed {}".format(treasureLabel(a.bag[-1])))
    goal = describeGoal(a)
    if goal != st.session_state["lastGoal"] and not a.escaped:
        events.append("new goal: {}".format(goal))
        st.session_state["lastGoal"] = goal
    if a.escaped:
        events.append("found the exit {}".format(exitIcon))
        st.session_state["celebrate"] = True
    elif not a.alive:
        events.append("dead (performance {})".format(a.performance))

    if a.state != st.session_state["visited"][-1]:
        st.session_state["visited"].append(a.state)
    st.session_state["log"].append({
        "Step": len(st.session_state["log"]) + 1,
        "Action": action,
        "Position": a.state,
        "Heading": "{} {}".format(arrows[a.heading], a.heading),
        "Performance": a.performance,
        "Event": "; ".join(events),
    })


def AgentRun():
    while st.session_state["env"].is_agent_alive(st.session_state["agent"]):
        AgentStep()


def describeGoal(agent):
    if agent.goal is None:
        return "-"
    if agent.goal == agent.exit:
        return "{} Exit ({})".format(exitIcon, agent.exit)
    if isinstance(agent.goal, list):
        return "the nearest treasure ({})".format(", ".join(agent.goal))
    return "{} at {}".format(treasureLabel(agent.target), agent.goal)


def buildGraph(env, agent, visited):
    #no font_color here: pyvis would replace the font (size) of every node with it
    net = Network(bgcolor="#242020", height="640px", width="100%", cdn_resources="remote")

    treasures = env.treasures_map()
    goals = agent.goal if isinstance(agent.goal, list) else [agent.goal]
    for node in env.status.nodes():
        x, y = env.status.getLocation(node)
        label = node
        color = nodeColors["default"]
        if node in visited:
            color = nodeColors["visited"]
        if node == mazeStart:
            color = nodeColors["start"]
        if node == mazeFinish:
            color = nodeColors["finish"]
            label = "{} {}".format(node, exitIcon)
        if node in treasures:
            color = nodeColors["treasure"]
            label = "{} {}".format(node, treasureTypes[treasures[node]][0])
        size = 16
        if node == agent.state:
            color = nodeColors["agent"]
            label = "🤖{} {}".format(arrows[agent.heading], node)
            size = 26
        border = nodeColors["goal"] if node in goals and agent.alive else color
        net.add_node(node, label=label, title=node, x=x * 115, y=y * 135, size=size, physics=False,
                     color={"background": color, "border": border}, borderWidth=6 if border != color else 1,
                     font={"size": 26, "color": "white"})

    path = list(zip(visited, visited[1:]))
    for node_source in env.status.nodes():
        for node_target in env.status.get(node_source):
            if node_source < node_target:
                used = (node_source, node_target) in path or (node_target, node_source) in path
                net.add_edge(node_source, node_target, color="orange" if used else "#9e9e9e", width=4 if used else 2)

    net.toggle_physics(False)
    html = net.generate_html().replace("</head>", "<style>body{margin:0;background:#242020} .card{border:none}</style></head>")
    if hasattr(st, "iframe"): #new Streamlit versions replace components.html with st.iframe
        st.iframe(html, height=645)
    else:
        components.html(html, height=645)


def showLegend():
    chips = [("Start", nodeColors["start"]), ("Finish " + exitIcon, nodeColors["finish"]), ("Treasure", nodeColors["treasure"]),
             ("Visited", nodeColors["visited"]), ("Agent 🤖", nodeColors["agent"]), ("Current goal (border)", nodeColors["goal"])]
    html = " ".join("<span style='display:inline-block;margin:2px 10px 2px 0'>"
                    "<span style='display:inline-block;width:12px;height:12px;border-radius:50%;background:{};"
                    "border:1px solid #888;vertical-align:middle'></span> {}</span>".format(c, t) for t, c in chips)
    st.markdown(html, unsafe_allow_html=True)


def sidebar():
    st.sidebar.header("Maze settings")
    st.sidebar.radio("Version (goal state)", versions, key="version", on_change=startGame,
                     captions=[goalDescriptions[v] for v in versions])
    if st.session_state["version"] == "Specific treasure":
        st.sidebar.selectbox("Treasure to find", ["nearest"] + list(treasureTypes), key="target", on_change=startGame,
                             format_func=lambda t: "Any (the nearest one)" if t == "nearest" else treasureLabel(t))
    st.sidebar.button("🎲 New maze (re-place treasures)", on_click=shuffleTreasures)
    st.sidebar.button("↺ Restart the Agent", on_click=startGame)

    st.sidebar.subheader("Treasures in the maze")
    agent = st.session_state["agent"]
    for node, name in sorted(st.session_state["placement"].items(), key=lambda t: t[1]):
        status = " ✅ grabbed" if name in agent.bag else ""
        st.sidebar.write("{} at **{}**{}".format(treasureLabel(name), node, status))


def main():
    st.set_page_config(page_title="Treasure Maze", page_icon="🪙", layout="wide")

    if "placement" not in st.session_state:
        st.session_state["placement"] = newPlacement()
        st.session_state["version"] = "Specific treasure"
        st.session_state["target"] = "nearest"
    if "agent" not in st.session_state:
        startGame()

    sidebar()
    env, agent = st.session_state["env"], st.session_state["agent"]

    # Set header title
    st.header("Problem Solving Agents: Treasure Maze")
    st.caption("Version: **{}** - {}. Breadth-First Search over the state (position, heading, treasures collected); "
               "actions: advance, left, right.".format(agent.version, goalDescriptions[agent.version]))

    graphCol, infoCol = st.columns([3, 2])
    with graphCol:
        st.subheader("State of the Environment", divider="red")
        buildGraph(env, agent, st.session_state["visited"])
        showLegend()

    with infoCol:
        st.subheader("The Agent", divider="red")
        c1, c2, c3 = st.columns(3)
        c1.metric("Position", agent.state)
        c2.metric("Heading", "{} {}".format(arrows[agent.heading], agent.heading))
        c3.metric("Performance", agent.performance)
        st.info("The Agent goal is: {}".format(describeGoal(agent)))
        bag = ", ".join(treasureLabel(t) for t in agent.bag) if agent.bag else "empty"
        st.info("Treasures grabbed: {}".format(bag))

        if agent.escaped:
            st.success("{} The Agent found the exit with performance {}.".format(exitIcon, agent.performance))
            if st.session_state.pop("celebrate", False):
                st.balloons()
        elif not agent.alive:
            st.error("Agent in location {} and it is dead (performance {}).".format(agent.state, agent.performance))
        else:
            if agent.seq:
                st.write("**Planned actions ({}):** {}".format(len(agent.seq), " → ".join(agent.seq)))
                if len(agent.seq) > agent.performance:
                    st.warning("The plan needs {} more actions, but the Agent's performance is only {}: "
                               "it will die on the way.".format(len(agent.seq), agent.performance))
            b1, b2 = st.columns(2)
            b1.button("Run One Agent's Step", on_click=AgentStep, type="primary")
            b2.button("Run to the end", on_click=AgentRun)

    if st.session_state["log"]:
        st.subheader("Executed actions", divider="gray")
        st.dataframe(pd.DataFrame(st.session_state["log"]), hide_index=True)

    with st.expander("How the Agent solves the maze"):
        st.markdown(f"""
* **State space:** a node for the start **S**, the finish **F** {exitIcon}, the dead end **F2** and every junction / turning point;
  the edges are corridors of the maze (cost 1). The second copies of the repeated labels in the task picture are named E2, F2, J2, L2.
* **State** = (position, heading, treasures collected). **Actions:** `advance` (go along the corridor in front),
  `left` / `right` (turn 90°). Turning around at a dead end = two turns.
* **Performance:** initially 50% of the number of nodes ({len(env.status.nodes())} // 2 = {len(env.status.nodes()) // 2}); every executed action costs 1.
  The Agent dies when its performance reaches 0.
* **Treasures:** placed randomly - never at S or F, one treasure per node. The Agent grabs a treasure when it steps on its node.
* **Specific treasure:** goal = the treasure's node; after the grab the Agent **re-defines its goal** to the exit and searches again.
* **Treasure collection:** one search with goal = (F, {{Gold, Diamond, Pizza, ExtraPoints}}): the Agent cannot stop at F before it has all 4 treasures.
* **Search:** Breadth-First Search (uninformed, FIFO frontier) - every action costs 1, so the plan has the fewest actions.
""")


if __name__ == '__main__':
    main()
