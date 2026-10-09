# CS3220 Lab 3 – Problem Solving Agents: Treasure Maze

## Run

```
pip install -r requirements.txt
streamlit run lab3app_treasureMaze.py
```

The solution is also in the notebook, section **Solution: Treasure Maze** (after the task description).

## Files

| File | What it does |
| --- | --- |
| `data/treasureMazeData.py` | The maze graph (nodes S, F, the dead end, junctions), node locations, the treasure types |
| `src/mazeGraphClass.py` | `MazeGraph(Graph)`: the graph plus the direction (N/E/S/W) of every corridor |
| `src/mazeProblemClass.py` | `MazeProblem(Problem)`: state = (position, heading, treasures collected); actions advance / left / right |
| `src/mazeProblemSolvingAgentClass.py` | The problem-solving agent (goal formulation, problem formulation, search, execution) for the 3 versions |
| `src/treasureMazeEnvironmentClass.py`, `src/treasureClass.py` | The Treasure Maze environment and the treasures |
| `src/PS_agentPrograms.py` | `BreadthFirstSearchAgentProgram` (uninformed search) was added |
| `lab3app_treasureMaze.py` | Streamlit web app |
| `src/naigationEnvironmentClass.py`, `src/agentClass.py`, `src/locations.py` | Modules imported by the tutorial and `lab3app_navExample.py` but missing from the starter code |

## Design

* **Maze graph.** Follows the task's state-space picture: 23 nodes and 30 corridors, each costing 1. The picture repeats four labels, so the second copies are named **E2, F2 (dead end), J2, L2**.
* **Actions.** `advance` moves along the corridor in front of the agent. `left` and `right` turn 90° in place, so turning around at a dead end takes two turns.
* **Performance.** Starts at 50% of the number of nodes (23 // 2 = 11). Each executed action costs 1, and the agent dies at 0.
* **Treasures.** Placed randomly, never at S or F, at most one per node. The agent grabs a treasure when it steps on its node.
* **Versions** (selectable in the app):
  * *Basic*: reach F.
  * *Specific treasure*: the goal is a chosen treasure, or the nearest one. After the grab, the agent **re-defines its goal** to the exit and searches again.
  * *Treasure collection*: one search with goal (F, {Gold, Diamond, Pizza, ExtraPoints}). The agent cannot stop at F until it has all 4 treasures.
* **Search.** Breadth-First Search. Every action costs 1, so each plan uses the fewest possible actions.
* **Note.** With a performance of 11, the optimal *Treasure collection* route is usually longer than 11 actions (median 18), so the agent normally dies on the way. The notebook shows it succeeding when given more performance.
