from src.problemClass import Problem


class LabMazeProblem(Problem):
  '''The Laboratory Maze Problem (Task 1).
  States:           the nodes of the LabGraph (the start, the target, the decision points)
  Actions:          the directions 0 left, 1 up, 2 right, 3 down that the robot can take at a node
  Transition model: RESULT(node, action) = the next node at the end of the corridor
  Action cost:      the sum of the costs of the moves along the corridor (left 2, up 4, right 2, down 1)
  Goal test:        the node is the rescue target'''

  def __init__(self, initial, goal, graph):
    super().__init__(initial, goal)
    self.graph = graph  # the state space - an instance of LabGraph

  def actions(self, state):
    return list(self.graph.origin[state].keys())

  def result(self, state, action):
    return self.graph.origin[state][action]

  def path_cost(self, cost_so_far, A, action, B):
    return cost_so_far + self.graph.cost(A, action)
