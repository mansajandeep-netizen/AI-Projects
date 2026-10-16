from src.maze2026GraphClass import mazeGraph
from src.mazeData import mazeStatesLocations
from src.labMazeData import actionCosts


class LabGraph(mazeGraph):
  '''The state-space graph of the laboratory (Task 1).
  Nodes: the starting position, the rescue target and every DECISION POINT -
         a cell where the robot can choose between 3 or 4 directions (a meaningful choice).
  Edges: the corridors that connect the nodes. A corridor that ends in a dead end is not an edge:
         it leads nowhere (the start and the target are nodes, so they are never lost).

  origin     = {node: {action: next node}}   the transition model between the nodes: at a node the robot
                                             chooses a direction (0-3) and follows the corridor to the next node
  corridors  = {(node, action): [moves]}     the single moves (0-3) the robot makes along the corridor
  graph_dict = {node: {next node: cost}}     the cost of a corridor = the sum of the costs of its moves'''

  def __init__(self, cellTM, start, target):
    self.cellTM = cellTM  # the transition model of the single moves: {cell: {action: next cell}}
    self.start = start
    self.target = target
    self.decisionPoints = sorted(cell for cell, actions in cellTM.items() if len(actions) >= 3)
    self.nodeSet = set(self.decisionPoints) | {start, target}

    self.corridors = {}
    origin = {}
    for node in sorted(self.nodeSet):
      origin[node] = {}
      for action in cellTM[node]:
        corridor = self.follow(node, action)
        if corridor is not None:
          nextNode, moves = corridor
          origin[node][action] = nextNode
          self.corridors[(node, action)] = moves

    super().__init__(origin, mazeStatesLocations(sorted(self.nodeSet)))

  def follow(self, node, action):
    '''Walk from node in the direction action along the corridor up to the next node.
    Returns (next node, moves) or None if the corridor is a dead end or comes back to node.'''
    moves = [action]
    previous, cell = node, self.cellTM[node][action]
    while cell not in self.nodeSet:
      # a corridor cell has at most 2 open neighbours: the robot came from one, so there is one way forward
      ways = [(a, c) for a, c in self.cellTM[cell].items() if c != previous]
      if not ways:  # a dead end
        return None
      a, c = ways[0]
      moves.append(a)
      previous, cell = cell, c
    if cell == node:  # the corridor is a loop that comes back to the same node
      return None
    return cell, moves

  def make_graph(self, graph_dict):
    '''graph_dict = {node: {next node: cost of the cheapest corridor between them}}'''
    for a in graph_dict.keys():
      for (act, b) in graph_dict[a].items():
        cost = self.cost(a, act)
        if self.get(a, b) is None or cost < self.get(a, b):
          self.connect(a, b, cost)

  def nodes(self):
    '''All nodes: the start, the target and the decision points'''
    return sorted(self.origin.keys())

  def moves(self, node, action):
    '''The single moves of the corridor that starts at node in the direction action'''
    return self.corridors[(node, action)]

  def cost(self, node, action):
    '''The cost of the corridor = the sum of the action costs (left 2, up 4, right 2, down 1)'''
    return sum(actionCosts[a] for a in self.corridors[(node, action)])

  def cells(self, node, action):
    '''The cells the robot passes through along the corridor (without node)'''
    cells, cell = [], node
    for a in self.corridors[(node, action)]:
      cell = self.cellTM[cell][a]
      cells.append(cell)
    return cells
