'''The refined PacMan World environment (Tasks 3, 5, 6).'''
import math
import random

from src.naigationEnvironmentClass import MazeNavigationEnvironment
from src.pacmanThings import Food, Ghost
from src.pacmanData import buildPacmanGraph, foodCells, WALL


class PacmanWorldEnvironment(MazeNavigationEnvironment):
    '''
    * Fixed Food Dots on the cells marked 2 in the maze (5% of the space)
    * n_ghosts Ghosts at random open cells - never on the start, the exit, a food
      dot or another ghost. Power = random integer in [20%, 30%] of the space cells.
    * every move costs the agent 1 performance point
    * eating a food dot doubles the performance (Task 5)
    * meeting a ghost -> fight: the agent wins only if performance > ghost power,
      then loses 10% of its performance; otherwise the agent is killed (Task 6)
    '''

    def __init__(self, maze, start, exit, n_ghosts=5, ghost_power_range=(0.2, 0.3),
                 seed=None, verbose=True):
        super().__init__(buildPacmanGraph(maze))
        self.maze = maze.copy()
        self.n = maze.shape[0]
        self.space_cells = self.n * self.n
        self.start, self.exit = start, exit
        self.verbose = verbose
        self.rng = random.Random(seed)
        self.time = 0
        self.things = []
        for cell in foodCells(maze):
            self.add_object(Food(), cell)
        self.place_ghosts(n_ghosts, ghost_power_range)

    # ------------------------------------------------------------- things
    def add_object(self, thing, location):
        thing.location = location
        self.things.append(thing)

    def place_ghosts(self, k, power_range):
        forbidden = {self.start, self.exit} | set(self.food_locations)
        candidates = [(i, j) for i in range(self.n) for j in range(self.n)
                      if self.maze[i, j] != WALL and (i, j) not in forbidden]
        lo = math.ceil(power_range[0] * self.space_cells)
        hi = math.floor(power_range[1] * self.space_cells)
        for cell in self.rng.sample(candidates, k):
            self.add_object(Ghost(self.rng.randint(lo, hi)), cell)

    @property
    def food_locations(self):
        return [t.location for t in self.things if isinstance(t, Food)]

    @property
    def ghosts(self):
        return [(t.location, t.power) for t in self.things if isinstance(t, Ghost)]

    def list_things_at(self, location, tclass=object):
        return [t for t in self.things if t.location == location and isinstance(t, tclass)]

    # ------------------------------------------------------------- agent loop
    def percept(self, agent):
        '''The agent sees its own cell and the things in it (it cannot see further).'''
        return agent.state, self.list_things_at(agent.state)

    def add_thing(self, agent, location=None):
        if agent in self.agents:
            print("Can't add the same agent twice")
            return
        agent(agent.state)  # the agent formulates goals + problems and searches a route
        self.agents.append(agent)
        self._log(agent, f"{agent.name} starts at {agent.state} with performance {agent.performance}")
        self.react(agent)   # there may be food on the start cell
        agent.history = [(0, agent.state, agent.performance)]

    def execute_action(self, agent, action):
        if not agent.alive or agent.done:
            return
        agent.state = self.status.origin[agent.state][action]  # transition model RESULT(s, a)
        agent.performance -= 1
        if self.verbose == 'steps':
            print(f"step {self.time}: {action:>5} -> {agent.state} | performance {agent.performance}")
        self.react(agent)
        self.update_agent_alive(agent)
        agent.history.append((self.time, agent.state, agent.performance))

    def react(self, agent):
        '''Perceive the current cell and let the agent react to what it recognises.'''
        location, things = self.percept(agent)
        for reaction, thing in agent.interpret_percept(things):
            if reaction == 'eat':
                before = agent.performance
                agent.performance = round(agent.performance * 2, 2)
                self.things.remove(thing)
                self._log(agent, f"ate food at {location}: performance {before} -> {agent.performance}",
                          ('food', location))
            elif reaction == 'fight':
                if agent.performance > thing.power:
                    before = agent.performance
                    agent.performance = round(agent.performance * 0.9, 2)
                    self.things.remove(thing)
                    self._log(agent, f"met a ghost (power {thing.power}) at {location} and WON: "
                                     f"performance {before} -> {agent.performance}", ('won', location))
                else:
                    agent.alive = False
                    self._log(agent, f"met a ghost (power {thing.power}) at {location} with performance "
                                     f"{agent.performance} and was KILLED", ('killed', location))
                    return

    def update_agent_alive(self, agent):
        if not agent.alive:
            return
        if agent.performance <= 0:
            agent.alive = False
            self._log(agent, f"ran out of performance at {agent.state} and died", ('dead', agent.state))
        elif not agent.seq:
            agent.done = True
            self._log(agent, f"reached the exit {agent.state} with performance {agent.performance}",
                      ('exit', agent.state))

    def _log(self, agent, text, event=None):
        if event:
            agent.events.append((self.time, *event, agent.performance))
        if self.verbose:
            print(f"t={self.time:>3} | {text}")

    def is_done(self):
        return all((not a.alive) or a.done for a in self.agents)

    def step(self):
        self.time += 1
        for agent in self.agents:
            if agent.alive and not agent.done and agent.seq:
                self.execute_action(agent, agent.seq.pop(0))

    def run(self, steps=1000):
        for _ in range(steps):
            if self.is_done():
                break
            self.step()
        for a in self.agents:
            status = 'reached the exit' if a.done else ('was killed' if not a.alive else 'still moving')
            if self.verbose:
                print(f"== {a.name} {status} after {self.time} steps, final performance {a.performance}")
