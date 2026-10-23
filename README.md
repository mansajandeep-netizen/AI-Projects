# CS3220 Lab 5 – Informed Search Strategies: PacMan World

## Run

```
pip install -r requirements.txt
jupyter notebook "Lab5_InformedSearchStrategies_Tutorial&tasks.ipynb"
```

The solution is in the notebook, section **Solutions** (after the task description). All cells have been run, so the results can be read without running anything. `PacmanWorld_Task2_route.html` is the interactive pyvis picture of the Task 2 route.

## Files

| File | What it does |
| --- | --- |
| `src/PS_agentPrograms.py` | `A_StarSearchAgentProgram` was refined (counts the expanded nodes, reports the path cost); `IDA_StarSearchAgentProgram` and `RBFSAgentProgram` were added |
| `src/heuristics.py` | Euclidean, Manhattan and the maze-cost heuristic; each one takes a single goal or a list of goals |
| `src/pacmanData.py` | The PacMan World generator (20% walls, 5% food), the graph builder, exact costs (Dijkstra), the best food order (brute force), and the pictures (matplotlib and pyvis) |
| `src/pacmanThings.py` | `Food(Thing)` and `Ghost(Thing)`, a ghost with a power |
| `src/pacmanAgentClass.py` | `PacmanAgent(MazeProblemSolvingAgentSMART)`: plans one route through every food dot and then the exit, and recognises food and ghosts in its percept |
| `src/pacmanEnvironmentClass.py` | `PacmanWorldEnvironment(MazeNavigationEnvironment)`: hidden ghosts, performance, eating and fights |
| `src/agents.py` | `PacmanAgentAstar`, `PacmanAgentIDAstar` and `PacmanAgentRBFS` were added |
| `src/thingClass.py` | Imported by `agentClass.py` but missing from the starter code |
| `PacmanWorld_Task2_route.html` | The Task 2 route as a pyvis network (made by the notebook) |

## Design

* **Step costs.** They come from `mazeGraph`: up 2, down 1, left 0, right 0. Sideways moves are free, so the Euclidean and the Manhattan distance can overestimate the real cost.
* **World.** 10 × 10 cells with 20 walls and 5 food dots (5% of the space) on random cells. The start and the exit may also get food. A world is used only if every food dot and the exit can be reached, and the same seed gives the same world.
* **Task 1.** A\* counts the nodes it expands and reports the path cost and the number of moves (also kept in `program.stats`). If two nodes have the same f, it takes the one with fewer moves first.
* **Task 2.** A\* with the Manhattan distance. On a route with several goals, each leg (start → goal 1, goal 1 → goal 2, …) gets its own colour.
* **Task 3.** 5 ghosts on random open cells, never on the start, the exit, a food dot or another ghost. A ghost's power is a random integer from 20% to 30% of the space cells. The agent does not know where the ghosts are: its percept is only its own cell.
* **Task 4.** Rational order: a single A\* search whose goal is the list of the remaining food dots stops at the cheapest one. The heuristic is h(n) = the minimum over the food dots of the maze-cost estimate, 2 per row up and 1 per row down (sideways moves are free). It never overestimates, so the first food dot found is the cheapest one to reach.
* **Tasks 5–6.** Performance starts at 40% of the space cells (40). Every move costs 1, and every food dot doubles the performance. Against a ghost, the agent wins only if its performance is greater than the ghost's power, and then loses 10%. Otherwise the ghost kills it.
* **Tasks 7–8.** IDA\* and RBFS follow the pseudocode, and both skip cells that are already on the current path (otherwise the free left/right moves would loop forever). The same `PacmanAgent` runs with each of them.
* **Starter-code fixes.** In the bottom-right corner, `defineMazeAvailableActions` had swapped the left and up checks, so Pac-Man could walk into a wall. A\* waited forever when its frontier became empty.

## Results

* **Heuristics (1000 random problems).** Average nodes expanded: Manhattan 12.7, Euclidean 16.3, maze-cost 15.3, uniform-cost search 36.5. Euclidean returned a path more expensive than the optimum in 5 problems, Manhattan in 2, and maze-cost in none.
* **Food order (300 random worlds).** Average route cost: listed order 29.8, cheapest food first 22.5, and the best of all orders 20.1. Cheapest-food-first found the best order in 60% of the worlds.
* **The notebook's world (seed 67).** The listed order costs 29 and the rational order 17, which is also the best order. Pac-Man beats two ghosts before it eats anything, then eats all 5 food dots and reaches the exit with performance 587.16 (A\*). IDA\* and RBFS end with 451.16: their routes cost the same (17) but take 59 moves instead of 43.
* **Ghosts.** In 300 random worlds Pac-Man was never killed: it starts above the strongest possible ghost (40 > 30), and every food dot doubles its performance. A Pac-Man that starts at 20 is killed by the first ghost it meets.
* **IDA\* and RBFS.** They find the same costs as A\* but repeat a lot of work. On the hardest problem found, A\* expanded 65 nodes, IDA\* 127,671 and RBFS 887,938.
