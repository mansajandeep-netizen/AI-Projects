# CS3220 Lab 4 – Uninformed Search Strategies: Rescue Robots in a Hazardous Laboratory

## Run

```
pip install -r requirements.txt
streamlit run lab4app_rescueRobots.py
```

The solution is also in the notebook `Lab4_UninformedSearchStrategies_Tutorial&tasks.ipynb`, section **Solution: Rescue Robots in the Hazardous Laboratory** (after the task description).

## Files

| File | What it does |
| --- | --- |
| `src/labMazeData.py` | The maze generator (7×7 NumPy matrix), the actions 0-3 and their costs, the transition model of the single moves |
| `src/labGraphClass.py` | `LabGraph(mazeGraph)`: the state-space graph – start, target, decision points and the corridors between them |
| `src/labMazeProblemClass.py` | `LabMazeProblem(Problem)`: actions, transition model and path cost on the graph |
| `src/securityDroneClass.py` | `SecurityDrone(Thing)` with a random attack power |
| `src/rescueRobotAgentClass.py` | `RescueRobotAgent(MazeProblemSolvingAgentSMART)`: state = (position, energy), the drones it has met |
| `src/labEnvironmentClass.py` | `LabEnvironment(environmentPro)`: moves, walls, boundaries, drones, Defense Mode, the winner |
| `src/PS_agentPrograms.py` | `UniformCostSearchAgentProgram` and `IDSearchAgentProgram` were added (+ `BestFirstSearch`, `DepthLimitedSearch`, `RecursiveDLS`) |
| `src/agents.py` | `RescueRobotAgentUCS` and `RescueRobotAgentIDS` were added |
| `src/labMazeVisual.py` | Pictures: the laboratory (matplotlib) and the networks (pyvis) |
| `src/rescueMission.py` | A whole mission from one seed: laboratory, graph, environment and both robots |
| `src/locations.py` | Imported by `environmentProClass.py` but missing from the starter code |
| `lab4app_rescueRobots.py` | Streamlit web app |
| `labMazeCells.html`, `labStateSpace.html` | The networks of the notebook's laboratory (made by the notebook) |

## Design

* **Laboratory.** A 7×7 NumPy matrix: 0 free cell, 1 wall/debris, 2 security drone, 3 rescue target, 4 start. It has 12 walls/debris (round(25% × 49)), 5 drones (round(10% × 49)), and the start and target on random free cells. By default new laboratories are made until the target can be reached. The same seed gives the same laboratory.
* **State-space graph.** It has a node for the start, the target and every decision point: a cell with 3-4 available actions. The edges are the corridors. At a node the robot chooses a direction and follows the corridor to the next node. Corridors that end in a dead end or loop back are dropped. The cost of a corridor is the sum of its action costs, so A → B and B → A can differ.
* **Actions.** 0 Left, 1 Up, 2 Right, 3 Down. Walls and the boundary of the laboratory block a move.
* **Energy = performance.** The robot starts with energy = the number of nodes in the state-space graph. Every move takes its action cost: Left 2, Up 4, Right 2, Down 1. At 0 the battery is exhausted.
* **Drones.** A drone's attack power is random, from 10% to 40% of the number of nodes. The robots don't know where the drones are; a drone becomes known when a robot enters its cell. If attack ≥ 2 × current energy, the drone captures the robot. Otherwise Defense Mode costs 10% of the current energy, and the new energy becomes part of the robot's state.
* **UCS Robot.** Best-First Search with f(n) = g(n) = path cost, so it always finds the cheapest plan.
* **IDDFS Robot.** `IDSearchAgentProgram` runs Depth-Limited Search with the limit 0, 1, 2, …, starting each time from the initial state. `RecursiveDLS` returns *cutoff* or *failure* as in the pseudo-code. It skips states that are already on the current path: the graph has cycles, and without this check it could never return failure. IDS stops at the first solution, or when DLS returns failure, which means no solution exists. Its plan has the fewest corridors, but it ignores the costs.
* **Winner.** The robot that reaches the target with the highest energy.
* **Results.** In the notebook's laboratory (seed 205) both plans have 6 corridors. UCS costs 16 and IDDFS 21. The IDDFS Robot is captured by its second drone, and the UCS Robot wins with energy 3.2. Over 1000 random laboratories the IDDFS plan was never cheaper than the UCS plan. Results: 616 ties, 143 UCS wins, 59 IDDFS wins (all with plans of equal cost, where the UCS path met more drones), and 182 with no winner.
* **Tutorial fix.** In the tutorial's network, pyvis kept only one edge per pair of cells (the edges were undirected), so the opposite action disappeared. `cellNetwork` draws every available action as its own directed, curved arrow with a label.
