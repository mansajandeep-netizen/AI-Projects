import collections

from src.problemSolvingAgentProgramClass import SimpleProblemSolvingAgentProgram
from src.mazeProblemClass import MazeProblem
from data.treasureMazeData import treasureTypes, startHeading

# 3 versions of the goal state
versions = ['Basic', 'Specific treasure', 'Treasure collection']

class MazeProblemSolvingAgent(SimpleProblemSolvingAgentProgram):
  '''Problem-Solving Agent for the Treasure Maze.
     Basic               - reach the finish
     Specific treasure   - grab one treasure (target, None = the nearest one), then re-define the goal: find the exit
     Treasure collection - collect ALL treasures and reach the finish: state = (position, heading, treasures collected)'''

  def __init__(self, initial_state=None, dataGraph=None, exitState=None, version='Basic', target=None, program=None):
    super().__init__(initial_state)
    self.dataGraph = dataGraph #instance of MazeGraph
    self.exit = exitState
    self.version = version
    self.target = target
    self.heading = startHeading
    self.goal = None #the current goal: a node or a list of nodes
    self.bag = [] #names of the grabbed treasures
    self.treasures = {} #{node: treasure name} - what the Agent percepts (the maze is fully observable)
    self.escaped = False

    self.performance = len(dataGraph.nodes()) // 2 #50% of the number of nodes

    if program is None or not isinstance(program, collections.abc.Callable):
      print("Can't find a valid program for {}, falling back to default.".format(self.__class__.__name__))

      def program(percept):
        return eval(input('Percept={}; action? '.format(percept)))

    self.program = program

  def __repr__(self):
    return '<MazeAgent ({})>'.format(self.version)

  def wants(self, treasure):
    #should the Agent grab this treasure?
    if self.version == 'Treasure collection':
      return True
    if self.version == 'Specific treasure':
      return not self.bag and (self.target is None or treasure == self.target)
    return False

  def objective_done(self):
    #may the Agent stop at the exit?
    if self.version == 'Treasure collection':
      return set(treasureTypes) <= set(self.bag)
    if self.version == 'Specific treasure':
      return len(self.bag) > 0
    return True

  def update_state(self, state, percept):
    location, heading, treasures = percept
    self.heading = heading
    self.treasures = dict(treasures)
    return location

  def formulate_goal(self, state):
    if self.version == 'Specific treasure' and not self.objective_done():
      if self.target is None:
        self.goal = list(self.treasures) #any treasure: the nearest one will be found
      else:
        spots = [node for node, name in self.treasures.items() if name == self.target]
        self.goal = spots[0] if spots else None
    else:
      self.goal = self.exit #the treasure is grabbed (or not needed) -> the goal is re-defined: find the exit
    print("Agent's goal: {}".format(self.goal))
    return self.goal

  #a description of the states and actions necessary to reach the goal
  def formulate_problem(self, state, goal):
    if self.version == 'Treasure collection':
      return MazeProblem((state, self.heading, frozenset(self.bag)), goal, self.dataGraph, self.treasures, treasureTypes)
    return MazeProblem((state, self.heading, frozenset()), goal, self.dataGraph)

  def search(self, problem):
    node = self.program(problem)
    if node is None:
      print("There is no solution for the goal {}".format(problem.goal))
      return []
    solution = node.solution()
    print("Solution (a sequence of actions) from the current state to the goal: {}".format(solution))
    return solution

  def plan(self, percept):
    '''Phases 1-3: goal formulation, problem formulation and search (only when the Agent has no plan)'''
    self.state = self.update_state(self.state, percept)
    if not self.seq:
      goal = self.formulate_goal(self.state)
      if goal is None or goal == []:
        return self.seq
      problem = self.formulate_problem(self.state, goal)
      self.seq = self.search(problem)
    return self.seq

  def __call__(self, percept):
    '''Phase 4: execution - one action of the plan at a time'''
    if not self.plan(percept):
      return None
    return self.seq.pop(0)
