# Lab 4 tasks: the Hazardous Laboratory Maze
# The laboratory is a square NumPy matrix:
#   0 = free cell, 1 = wall/debris, 2 = security drone, 3 = rescue target, 4 = robot starting position
import numpy as np

from src.mazeData import LEFT, UP, RIGHT, DOWN, actions_dict

FREE = 0
WALL = 1
DRONE = 2
TARGET = 3
START = 4

cellTypes = {
    FREE: 'free cell',
    WALL: 'wall/debris',
    DRONE: 'security drone',
    TARGET: 'rescue target',
    START: 'starting position',
}

# the 4 movement actions of the robot: action -> (row change, column change)
moves = {
    LEFT: (0, -1),
    UP: (-1, 0),
    RIGHT: (0, 1),
    DOWN: (1, 0),
}

# the cost of every action (Task 2); a move takes this much energy from the robot's battery
actionCosts = {
    LEFT: 2,
    UP: 4,
    RIGHT: 2,
    DOWN: 1,
}


def makeLabMaze(n=7, wallRate=0.25, droneRate=0.10, seed=None, solvable=True):
  '''A random n x n laboratory (NumPy matrix): 25% walls/debris, 10% security drones,
  the starting position and the rescue target on two of the remaining free cells.
  seed     - the same seed gives the same laboratory (None = a new laboratory on every run)
  solvable - make new laboratories until the target can be reached from the start'''
  rng = np.random.default_rng(seed)
  cells = [(i, j) for i in range(n) for j in range(n)]
  nWalls = round(wallRate * n * n)    # 7x7: 12 cells
  nDrones = round(droneRate * n * n)  # 7x7: 5 cells
  while True:
    order = [cells[k] for k in rng.permutation(len(cells))]  # all cells in a random order
    maze = np.full((n, n), FREE)
    for cell in order[:nWalls]:
      maze[cell] = WALL
    for cell in order[nWalls:nWalls + nDrones]:
      maze[cell] = DRONE
    start, target = order[nWalls + nDrones], order[nWalls + nDrones + 1]  # two free cells
    maze[start] = START
    maze[target] = TARGET
    if not solvable or isReachable(makeLabTransitionModel(defineLabAvailableActions(maze)), start, target):
      return maze


def labMazeCells(maze, cellType):
  '''All cells (row, column) of the given type'''
  return [(int(i), int(j)) for i, j in zip(*np.where(maze == cellType))]


def findCell(maze, cellType):
  '''The first cell of the given type (used for the start and the target)'''
  cells = labMazeCells(maze, cellType)
  return cells[0] if cells else None


def robotMap(maze):
  '''The laboratory as the robot knows it: the drones are unknown, so for the robot they are free cells'''
  known = maze.copy()
  known[known == DRONE] = FREE
  return known


def defineLabAvailableActions(maze):
  '''{cell: [available actions]} for every cell that is not a wall/debris.
  An action is available if it doesn't lead out of the laboratory or into a wall/debris.
  A security drone doesn't block a cell: the robot can enter it.'''
  n = maze.shape[0]
  availableActions = {}
  for i in range(n):
    for j in range(n):
      if maze[i, j] == WALL:
        continue
      availableActions[(i, j)] = []
      for action, (di, dj) in moves.items():
        x, y = i + di, j + dj
        if 0 <= x < n and 0 <= y < n and maze[x, y] != WALL:
          availableActions[(i, j)].append(action)
  return availableActions


def makeLabTransitionModel(availableActions):
  '''The transition model of the single moves: {cell: {action: next cell}}'''
  transitionModel = {}
  for (i, j), actions in availableActions.items():
    transitionModel[(i, j)] = {}
    for action in actions:
      di, dj = moves[action]
      transitionModel[(i, j)][action] = (i + di, j + dj)
  return transitionModel


def labResult(transitionModel, cell, action):
  '''RESULT(s, a) for any of the 4 actions.
  A wall/debris or the boundary of the laboratory blocks the move: the robot stays in its cell.'''
  return transitionModel[cell].get(action, cell)


def isReachable(transitionModel, start, target):
  '''Can the robot get from start to target? Only the walls matter, the drones don't block the way.'''
  reached = {start}
  frontier = [start]
  while frontier:
    cell = frontier.pop()
    if cell == target:
      return True
    for nextCell in transitionModel[cell].values():
      if nextCell not in reached:
        reached.add(nextCell)
        frontier.append(nextCell)
  return False


def actionName(action):
  '''2 -> '2 (right)' '''
  return '{} ({})'.format(action, actions_dict[action])
