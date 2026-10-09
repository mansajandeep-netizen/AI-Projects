import collections

from src.problemSolvingAgentProgramClass import SimpleProblemSolvingAgentProgram
from src.mazeProblemClass import MazeProblem
from data.treasureMazeData import treasureTypes, startHeading

# the 3 versions of the goal state
versions = ['Basic', 'Specific treasure', 'Treasure collection']

class MazeProblemSolvingAgent(SimpleProblemSolvingAgentProgram):
  '''Problem-Solving Agent for the Treasure Maze.
     Basic               - reach the finish
     Specific treasure   - grab one treasure (target; None = the nearest one),
                           then re-define the goal: find the exit
     Treasure collection - collect ALL treasures and reach the finish

  The 4 phases of a problem-solving agent:
     1. formulate_goal    - what do I want to reach?
     2. formulate_problem - describe it as a MazeProblem
     3. search            - BFS finds the list of actions
     4. __call__          - do the actions one by one'''

  def __init__(self, initial_state=None, dataGraph=None, exitState=None, version='Basic', target=None, program=None):
    super().__init__(initial_state)
    self.dataGraph = dataGraph   # the maze: a MazeGraph
    self.exit = exitState        # the finish node, 'F'
    self.version = version       # one of `versions`
    self.target = target         # Specific treasure only: the treasure to find (None = the nearest one)
    self.heading = startHeading  # where the Agent is looking
    self.goal = None             # the current goal: a node, or a list of nodes
    self.bag = []                # names of the treasures the Agent has grabbed
    self.treasures = {}          # where the treasures are: {node: treasure name} (the maze is fully observable)
    self.escaped = False         # True when the Agent got out of the maze

    self.performance = len(dataGraph.nodes()) // 2  # 50% of the number of nodes

    # the same check as in the other agents of the course
    if program is None or not isinstance(program, collections.abc.Callable):
      print("Can't find a valid program for {}, falling back to default.".format(self.__class__.__name__))

      def program(percept):
        return eval(input('Percept={}; action? '.format(percept)))

    self.program = program  # the search algorithm (BFS)

  def __repr__(self):
    return '<MazeAgent ({})>'.format(self.version)

  def wants(self, treasure):
    '''Should the Agent grab this treasure?'''
    if self.version == 'Treasure collection':
      return True                       # grab everything

    if self.version == 'Specific treasure':
      if self.bag:
        return False                    # it already has its one treasure
      if self.target is None:
        return True                     # any treasure is fine
      return treasure == self.target    # only the chosen one

    return False                        # Basic: treasures are ignored

  def objective_done(self):
    '''May the Agent stop at the exit?'''
    if self.version == 'Treasure collection':
      for name in treasureTypes:
        if name not in self.bag:
          return False                  # a treasure is still missing
      return True

    if self.version == 'Specific treasure':
      return len(self.bag) > 0          # it has its treasure

    return True                         # Basic: just reach the exit

  def update_state(self, state, percept):
    '''Read the percept: (position, heading, where the treasures are).'''
    location, heading, treasures = percept
    self.heading = heading
    self.treasures = dict(treasures)
    return location

  # Phase 1
  def formulate_goal(self, state):
    if self.version == 'Specific treasure' and not self.objective_done():
      # first goal: the treasure's node
      if self.target is None:
        self.goal = list(self.treasures)  # all treasure nodes: BFS will reach the nearest one
      else:
        self.goal = None                  # stays None if the target is not in the maze
        for node, name in self.treasures.items():
          if name == self.target:
            self.goal = node
            break
    else:
      # the treasure is grabbed (or not needed) -> the goal is re-defined: find the exit
      self.goal = self.exit

    print("Agent's goal: {}".format(self.goal))
    return self.goal

  # Phase 2: a description of the states and actions necessary to reach the goal
  def formulate_problem(self, state, goal):
    if self.version == 'Treasure collection':
      # the state also remembers the treasures: the Agent can't stop at F before it has all 4
      start = (state, self.heading, frozenset(self.bag))
      return MazeProblem(start, goal, self.dataGraph, treasures=self.treasures, wanted=treasureTypes)

    start = (state, self.heading, frozenset())
    return MazeProblem(start, goal, self.dataGraph)

  # Phase 3
  def search(self, problem):
    node = self.program(problem)  # BFS returns the goal node of the search tree (or None)
    if node is None:
      print("There is no solution for the goal {}".format(problem.goal))
      return []
    solution = node.solution()    # the list of actions from the start to the goal
    print("Solution (a sequence of actions) from the current state to the goal: {}".format(solution))
    return solution

  def plan(self, percept):
    '''Phases 1-3. The Agent plans only when it has no plan left.'''
    self.state = self.update_state(self.state, percept)

    if not self.seq:
      goal = self.formulate_goal(self.state)
      if goal is None or goal == []:
        return self.seq  # nothing to search for
      problem = self.formulate_problem(self.state, goal)
      self.seq = self.search(problem)

    return self.seq

  # Phase 4
  def __call__(self, percept):
    '''Execution: return the next action of the plan (None = no plan).'''
    if not self.plan(percept):
      return None
    return self.seq.pop(0)
