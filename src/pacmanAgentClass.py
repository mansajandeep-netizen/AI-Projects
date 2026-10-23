'''The Pac-Man problem-solving agent (Tasks 2, 4, 5, 6).'''
from src.mazeProblemSolvingAgentSMARTClass import MazeProblemSolvingAgentSMART
from src.mazeProblemClass import MazeProblem
from src.pacmanThings import Food, Ghost


class PacmanAgent(MazeProblemSolvingAgentSMART):
    '''A problem-solving agent with a SET of goals: every Fixed Food Dot, then the exit.

    initial_state - start cell
    dataGraph     - the mazeGraph of the world
    foods         - the food cells (food dots are fixed and visible, ghosts are not)
    exitState     - the finish cell
    program       - the search program (A*, IDA* or RBFS from src/PS_agentPrograms.py)
    space_cells   - number of cells in the maze (n*n); start performance = 40% of it (Task 5)
    rational      - False: visit the food in the order it is listed (Task 2)
                    True : always go next to the CHEAPEST food dot to reach (Task 4)
    '''

    def __init__(self, initial_state, dataGraph, foods, exitState, program,
                 space_cells, rational=True, name='Pac-Man', verbose=True):
        super().__init__(initial_state, dataGraph, exitState, program)
        self.start = initial_state
        self.foods = list(foods)
        self.exit = exitState
        self.rational = rational
        self.name = name
        self.verbose = verbose
        self.space_cells = space_cells
        self.performance = round(0.4 * space_cells)  # Task 5: 40% of the space cells
        self.segments = []   # one entry per leg of the route
        self.planned = False
        self.done = False
        self.history = []    # filled in by the environment while the agent moves
        self.events = []

    def __repr__(self):
        return f'<{self.name}>'

    # ------------------------------------------------------------- planning
    def __call__(self, percept):
        '''Called by the environment when the agent is added: plan the whole route.'''
        self.state = self.update_state(self.state, percept)
        if self.planned:
            print("I have already planned my route.")
            return None
        self.plan_route()
        return None

    def plan_route(self):
        current = self.state
        # food on the start cell is eaten immediately, food on the exit is eaten at the end
        remaining = [f for f in self.foods if f != current and f != self.exit]
        while remaining:
            # rational: ONE search whose goal is the whole list -> stops at the cheapest food
            goal = list(remaining) if self.rational else remaining[0]
            node = self.program(MazeProblem(current, goal, self.dataGraph))
            if node is None:
                print(f"{self.name}: cannot reach {goal} - skipped")
                if self.rational:
                    break
                remaining.pop(0)
                continue
            self._add_leg(node, 'food')
            passed = [s.state for s in node.path()]
            remaining = [f for f in remaining if f not in passed]  # food passed on the way is eaten too
            current = node.state
        node = self.program(MazeProblem(current, self.exit, self.dataGraph))
        if node is not None:
            self._add_leg(node, 'exit')
        self.seq = [a for leg in self.segments for a in leg['actions']]
        self.planned = True
        if self.verbose:
            self.print_plan()

    def _add_leg(self, node, kind):
        path = [n.state for n in node.path()]
        stats = dict(getattr(self.program, 'stats', {}))
        k = len(self.segments) + 1
        cell = lambda c: f'({c[0]},{c[1]})'
        target = 'exit' if kind == 'exit' else f'food {cell(node.state)}'
        self.segments.append({
            'kind': kind, 'goal': node.state, 'path': path, 'actions': node.solution(),
            'cost': node.path_cost, 'steps': node.depth,
            'expanded': stats.get('nodes_expanded'), 'stats': stats,
            'label': f'leg {k}: {cell(path[0])} → {target}'})

    # ------------------------------------------------------------- summary
    @property
    def total_cost(self):
        return sum(s['cost'] for s in self.segments)

    @property
    def total_steps(self):
        return sum(s['steps'] for s in self.segments)

    @property
    def total_expanded(self):
        return sum(s['expanded'] or 0 for s in self.segments)

    @property
    def food_order(self):
        '''{food cell: order in which it is eaten}'''
        order, k = {}, 0
        if self.start in self.foods:
            k += 1
            order[self.start] = k
        for seg in self.segments:
            for cell in seg['path'][1:]:
                if cell in self.foods and cell not in order:
                    k += 1
                    order[cell] = k
        return order

    def print_plan(self):
        print(f"{self.name} route plan ({'rational' if self.rational else 'given order'}):")
        for k, s in enumerate(self.segments, 1):
            print(f"  leg {k}: {s['path'][0]} -> {s['goal']} ({s['kind']}) | cost {s['cost']} "
                  f"| steps {s['steps']} | nodes expanded {s['expanded']}")
        print(f"  TOTAL: cost {self.total_cost} | steps {self.total_steps} "
              f"| nodes expanded {self.total_expanded}")

    # ------------------------------------------------------------- perception
    def interpret_percept(self, things):
        '''Task 6: the agent recognises the TYPE of each thing in its cell
        and decides how to react to it.'''
        reactions = []
        for t in things:
            if isinstance(t, Ghost):
                reactions.append(('fight', t))
            elif isinstance(t, Food):
                reactions.append(('eat', t))
        return reactions
