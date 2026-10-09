import random

from src.environmentProClass import environmentPro
from src.problemSolvingAgentProgramClass import SimpleProblemSolvingAgentProgram
from src.mazeGraphClass import turn
from src.treasureClass import Treasure

class TreasureMazeEnvironment(environmentPro):
  '''The Treasure Maze environment:
       status - the maze graph (MazeGraph)
       things - the treasures
       agents - the Problem-Solving Agent'''

  def __init__(self, mazeGraph, start, finish, treasureNames=None):
    super().__init__()
    self.status = mazeGraph
    self.start = start
    self.finish = finish
    if treasureNames:
      self.place_treasures(treasureNames)

  def valid_treasure_locations(self):
    '''All nodes except the start and the finish (a treasure can't be placed there).'''
    spots = []
    for node in self.status.nodes():
      if node != self.start and node != self.finish:
        spots.append(node)
    return sorted(spots)

  def place_treasures(self, treasureNames):
    '''Put every treasure at a random valid node.
    random.sample picks DIFFERENT nodes, so no two treasures share a node.'''
    spots = random.sample(self.valid_treasure_locations(), len(treasureNames))
    for name, spot in zip(treasureNames, spots):
      self.add_thing(Treasure(name), spot)

  def treasures_map(self):
    '''Where the treasures are now: {node: treasure name}'''
    result = {}
    for thing in self.things:
      if isinstance(thing, Treasure):
        result[thing.location] = thing.name
    return result

  def add_thing(self, thing, location=None):
    # adding the Agent
    if isinstance(thing, SimpleProblemSolvingAgentProgram):
      if thing in self.agents:
        print("Can't add the same agent twice")
        return
      thing.location = thing.state
      self.agents.append(thing)
      print("The Agent in {} facing {} with performance {}".format(thing.state, thing.heading, thing.performance))
      thing.plan(self.percept(thing))  # the Agent formulates its goal and the problem, then searches for a solution
      return

    # adding a treasure: only at a valid node, and at most one treasure per node
    if location not in self.valid_treasure_locations() or self.list_things_at(location, Treasure):
      print("Can't place {} at {}".format(thing, location))
      return
    super().add_thing(thing, location)

  def percept(self, agent):
    '''The maze is fully observable: the Agent knows its position, its heading and where the treasures are.'''
    return agent.state, agent.heading, self.treasures_map()

  def is_done(self):
    return not any(agent.alive for agent in self.agents)

  def execute_action(self, agent, action):
    if not self.is_agent_alive(agent):
      return

    # 1. no action = the Agent has no plan, it stops
    if action is None:
      print("Agent {} has no plan and stops in {}".format(agent, agent.state))
      agent.alive = False
      return

    # 2. do the action
    if action == 'advance':
      next_node = self.status.neighbor(agent.state, agent.heading)
      if next_node is None:
        print("Bump! There is a wall in front of the Agent")
      else:
        agent.state = next_node
        agent.location = next_node
    elif action == 'left' or action == 'right':
      agent.heading = turn(agent.heading, action)

    # 3. every executed action costs 1
    agent.performance -= 1
    print("Agent in {} facing {} with performance = {}".format(agent.state, agent.heading, agent.performance))

    # 4. grab a treasure if the Agent wants the one lying here
    self.grab_treasure(agent)

    # 5. did the Agent get out? If not, is it still alive (performance > 0)?
    if agent.state == self.finish and agent.objective_done():
      agent.escaped = True
      agent.alive = False  # its work is done
      print("Agent found the exit with performance {} and treasures {}".format(agent.performance, agent.bag))
    else:
      self.update_agent_alive(agent)

    # 6. the plan is finished (e.g. the treasure is grabbed): the Agent re-defines its goal and plans again
    if agent.alive and not agent.seq:
      agent.plan(self.percept(agent))

  def grab_treasure(self, agent):
    for treasure in self.list_things_at(agent.state, Treasure):
      if agent.wants(treasure.name):
        agent.bag.append(treasure.name)
        self.delete_thing(treasure)  # the treasure leaves the maze
        print("Agent grabbed the {}!".format(treasure))

  def step(self):
    '''One time step: every living Agent chooses an action and the environment executes it.'''
    if self.is_done():
      print("There is no one here who could work...")
      return []

    actions = []
    for agent in self.agents:
      if agent.alive:
        action = agent(self.percept(agent))
        print("Agent decided to do {}.".format(action))
        self.execute_action(agent, action)
        actions.append(action)
    return actions

  def run(self, steps=100):
    for step in range(steps):
      if self.is_done():
        return
      print("step {0}:".format(step+1))
      self.step()
