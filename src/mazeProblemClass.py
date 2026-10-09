from src.problemClass import Problem
from src.mazeGraphClass import turn

class MazeProblem(Problem):
    '''
    The Treasure Maze problem.
    The state is a tuple: (node, heading, collected)
        node      - the current position in the maze (a node of MazeGraph)
        heading   - where the Agent is looking: 'N', 'E', 'S' or 'W'
        collected - frozenset of the treasures the Agent has already grabbed
    Actions: 'advance' (go along the corridor in front of the Agent), 'left' and 'right' (turn 90 degrees).
    The goal is a node (or a list of nodes) that has to be reached after ALL treasures from `wanted` are collected:
        Basic               -> goal='F', wanted={}
        Specific treasure   -> goal=node of that treasure, then (re-defined goal) goal='F'
        Treasure collection -> goal='F', wanted={Gold, Diamond, Pizza, ExtraPoints}
    '''

    def __init__(self, initial, goal, graph, treasures=None, wanted=()):
        super().__init__(initial, goal)
        self.graph = graph #The state space - instance of MazeGraph
        self.treasures = treasures or {} #{node: treasure name}
        self.wanted = frozenset(wanted)

    def actions(self, state):
        node, heading, collected = state
        acts = ['left', 'right']
        if self.graph.neighbor(node, heading) is not None: #there is no wall in front of the Agent
            acts.insert(0, 'advance')
        return acts

    def result(self, state, action):
        #A transition model
        node, heading, collected = state
        if action in ('left', 'right'):
            return (node, turn(heading, action), collected)
        next_node = self.graph.neighbor(node, heading)
        treasure = self.treasures.get(next_node)
        if treasure in self.wanted: #the Agent grabs the treasure as soon as it gets to the node
            collected = collected | {treasure}
        return (next_node, heading, collected)

    def goal_test(self, state):
        node, heading, collected = state
        goals = self.goal if isinstance(self.goal, list) else [self.goal]
        return node in goals and self.wanted <= collected

    #path_cost of the parent class: every action costs 1
