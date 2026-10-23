'''Heuristic functions h(n) for the PacMan World.

Every heuristic has the signature  h(state, goal) -> number
where `goal` is either ONE cell (row, col) or a LIST of cells.
For a list of goals the heuristic returns the estimate to the NEAREST goal:
    h(n) = min over goals g of h(n, g)
This lets one A* run look for "the closest of several food dots".

Reminder - the step costs used by mazeGraph (src/maze2025GraphClass.py):
    up = 2,  down = 1,  left = 0,  right = 0
'''
import math


def _goals(goal):
    return goal if isinstance(goal, list) else [goal]


def euclideanDistance(state, goal):
    '''Straight-line distance  sqrt((x1-x2)^2 + (y1-y2)^2)  (the tutorial heuristic).'''
    return min(math.dist(state, g) for g in _goals(goal))


def manhattanDistance(state, goal):
    '''Grid distance  |x1-x2| + |y1-y2|  (Task 2).'''
    return min(sum(abs(a - b) for a, b in zip(state, g)) for g in _goals(goal))


def mazeCostHeuristic(state, goal):
    '''Cost-aware heuristic designed for this maze (Task 4).

    Left/right moves are free, so only the vertical distance has a guaranteed price:
      * goal is ABOVE the agent  -> at least (row - goalRow) "up" moves, 2 each
      * goal is BELOW the agent  -> at least (goalRow - row) "down" moves, 1 each
    It never overestimates the real cost (admissible) and it is consistent,
    so A* with it always returns a cheapest path - and with a list of goals
    the first goal A* reaches is the cheapest food dot to get to.
    '''
    best = math.inf
    for g in _goals(goal):
        dr = state[0] - g[0]
        h = 2 * dr if dr > 0 else -dr
        best = min(best, h)
    return best


def zeroHeuristic(state, goal):
    '''h(n) = 0  ->  A* becomes Uniform-Cost Search (used as the "true optimum" reference).'''
    return 0
