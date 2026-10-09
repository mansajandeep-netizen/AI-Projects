from src.problemClass import Problem
from src.mazeGraphClass import turn

class MazeProblem(Problem):
    '''
    The Treasure Maze problem.

    A state is a tuple (node, heading, collected):
        node      - where the Agent is, e.g. 'S'
        heading   - where the Agent is looking: 'N', 'E', 'S' or 'W'
        collected - frozenset of the treasures the Agent has grabbed, e.g. frozenset({'Gold'})
    Example of a state: ('S', 'E', frozenset())

    Actions: 'advance' - go along the corridor in front of the Agent
             'left'    - turn 90 degrees to the left
             'right'   - turn 90 degrees to the right

    Goal: be at the goal node (or one of the goal nodes, if goal is a list)
          AND hold every treasure from `wanted`.
        Basic               -> goal = 'F',              wanted = nothing
        Specific treasure   -> goal = the treasure's node, then (the goal is re-defined) goal = 'F'
        Treasure collection -> goal = 'F',              wanted = all 4 treasures
    '''

    def __init__(self, initial, goal, graph, treasures=None, wanted=()):
        super().__init__(initial, goal)
        self.graph = graph                 # the state space: a MazeGraph
        self.treasures = treasures or {}   # where the treasures are: {node: treasure name}
        self.wanted = frozenset(wanted)    # the treasures that must be collected

    def actions(self, state):
        node, heading, collected = state
        acts = []
        if self.graph.neighbor(node, heading) is not None:  # no wall in front of the Agent
            acts.append('advance')
        acts.append('left')   # turning is always possible
        acts.append('right')
        return acts

    def result(self, state, action):
        '''The transition model: the state after doing `action` in `state`.'''
        node, heading, collected = state

        if action == 'left' or action == 'right':
            new_heading = turn(heading, action)
            return (node, new_heading, collected)

        # 'advance': go to the next node
        next_node = self.graph.neighbor(node, heading)
        treasure = self.treasures.get(next_node)  # None if there is no treasure there
        if treasure in self.wanted:
            # the Agent grabs the treasure as soon as it gets to the node
            # (a frozenset can't be changed, so | makes a new one with the treasure added)
            collected = collected | {treasure}
        return (next_node, heading, collected)

    def goal_test(self, state):
        node, heading, collected = state

        if isinstance(self.goal, list):
            goals = self.goal
        else:
            goals = [self.goal]

        at_goal = node in goals
        has_all_wanted = self.wanted.issubset(collected)
        return at_goal and has_all_wanted

    # path_cost comes from the parent class Problem: every action costs 1
