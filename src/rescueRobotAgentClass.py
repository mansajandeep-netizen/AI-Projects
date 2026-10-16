from src.mazeProblemSolvingAgentSMARTClass import MazeProblemSolvingAgentSMART
from src.labMazeProblemClass import LabMazeProblem


class RescueRobotAgent(MazeProblemSolvingAgentSMART):
  '''The Rescue Robot: a Problem-Solving Agent (Tasks 1-2).
  state = (position, energy): the battery/energy level is the robot's performance and a part of its state.
  The robot knows the walls of the laboratory (the state-space graph LabGraph),
  but not the security drones: a drone becomes known when the robot enters its cell.'''

  def __init__(self, initial_state=None, dataGraph=None, goal=None, program=None, name='Rescue Robot', energy=None):
    # the parent sets performance = the number of nodes in the state-space graph: a full battery
    super().__init__(initial_state, dataGraph, goal, program)
    if energy is not None:
      self.performance = energy
    self.state = (initial_state, self.performance)
    self.name = name
    self.knownDrones = {}        # {cell: attack power} - the drones the robot has met
    self.path = [initial_state]  # the cells the robot has visited
    self.solution = None         # the goal node of the search tree (None = no solution)
    self.status = 'planning'

  def __repr__(self):
    return '<{}>'.format(self.name)

  @property
  def position(self):
    return self.state[0]

  @property
  def energy(self):
    return self.state[1]

  def update_state(self, state, percept):
    '''percept = (position, energy, the attack power of the drone in this cell or None)'''
    position, energy = percept[0], percept[1]
    if len(percept) > 2 and percept[2] is not None:
      self.knownDrones[position] = percept[2]  # the drone is not unknown anymore
    return (position, energy)

  #a description of the states and actions necessary to reach the goal
  def formulate_problem(self, state, goal):
    position, energy = state
    return LabMazeProblem(position, goal, self.dataGraph)

  def search(self, problem):
    '''Search for a path through the nodes of the graph,
    then turn it into the single moves (0-3) the robot has to make'''
    self.solution = self.program(problem)
    if self.solution is None:
      print("{}: no solution - the rescue target {} can't be reached from {}".format(self, problem.goal, problem.initial))
      return []
    seq = []
    for node in self.solution.path()[1:]:
      seq.extend(self.dataGraph.moves(node.parent.state, node.action))
    print("{}: path through the nodes {}".format(self, self.nodePath()))
    print("{}: solution (a sequence of actions) {}, path cost = {}".format(self, seq, self.solution.path_cost))
    return seq

  def nodePath(self):
    '''The nodes of the state-space graph on the planned path'''
    if self.solution is None:
      return []
    return [node.state for node in self.solution.path()]

  def corridorPath(self):
    '''The corridors of the planned path: [(node, action), ...]'''
    if self.solution is None:
      return []
    return [(node.parent.state, node.action) for node in self.solution.path()[1:]]

  def plannedCells(self):
    '''All cells of the planned path (from the start to the target)'''
    if self.solution is None:
      return [self.path[0]]
    cells = [self.solution.path()[0].state]
    for node in self.solution.path()[1:]:
      cells.extend(self.dataGraph.cells(node.parent.state, node.action))
    return cells

  def report(self):
    '''The result of the mission'''
    return {
        'Agent': self.name,
        'Reached target': self.status == 'target reached',
        'Status': self.status,
        'Energy (performance)': self.performance,
        'Moves': len(self.path) - 1,
        'Planned path cost': self.solution.path_cost if self.solution else None,
        'Drones met': len(self.knownDrones),
    }
