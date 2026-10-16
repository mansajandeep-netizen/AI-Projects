import random

from src.environmentProClass import environmentPro
from src.problemSolvingAgentProgramClass import SimpleProblemSolvingAgentProgram
from src.securityDroneClass import SecurityDrone
from src.labMazeData import DRONE, TARGET, actionCosts, actionName, labMazeCells, findCell


class LabEnvironment(environmentPro):
  '''The Hazardous Laboratory.
  status - the laboratory matrix, things - the security drones, agents - the Rescue Robots'''

  def __init__(self, maze, cellTM, nodesCount, seed=None):
    super().__init__()
    self.status = maze
    self.cellTM = cellTM
    self.target = findCell(maze, TARGET)
    rng = random.Random(seed)
    for cell in labMazeCells(maze, DRONE):
      self.add_thing(SecurityDrone(nodesCount, rng), cell)

  def add_thing(self, thing, location=None):
    if isinstance(thing, SimpleProblemSolvingAgentProgram):
      if thing in self.agents:
        print("Can't add the same agent twice")
        return
      self.agents.append(thing)
      print("{} starts in {} with energy {}".format(thing, thing.position, thing.performance))
      thing(self.percept(thing))
      if thing.seq:
        thing.status = 'on the way'
      else:
        thing.alive = False
        thing.status = 'no solution'
      return
    super().add_thing(thing, location)

  def droneAt(self, cell):
    drones = self.list_things_at(cell, SecurityDrone)
    return drones[0] if drones else None

  def percept(self, agent):
    '''(position, energy, attack power of the drone in the robot's cell or None)'''
    drone = self.droneAt(agent.position)
    return agent.position, agent.performance, drone.attackPower if drone else None

  def execute_action(self, agent, action):
    '''One move: 0 left, 1 up, 2 right, 3 down'''
    if not self.is_agent_alive(agent):
      return

    position = agent.position
    nextCell = self.cellTM[position].get(action)
    if nextCell is None:
      print("{} bumped into a wall/boundary and stays in {}".format(agent, position))
    else:
      position = nextCell
    agent.path.append(position)

    energy = round(agent.performance - actionCosts[action], 2)
    print("{} in {} with energy = {}".format(agent, position, max(energy, 0)))
    drone = self.droneAt(position)
    if energy <= 0:
      energy = 0
      agent.alive = False
      agent.status = 'battery exhausted'
      print("{}: the battery is exhausted in {}".format(agent, position))
    elif drone is not None:
      print("{} met a security drone with attack power {} in {}".format(agent, drone.attackPower, position))
      if drone.attackPower >= 2 * energy:  # defensive capability = current energy
        agent.alive = False
        agent.status = 'captured by a drone'
        print("The drone captured {}: attack power {} >= 2 x energy {}".format(agent, drone.attackPower, energy))
      else:
        defended = round(0.9 * energy, 2)
        print("{} activates Defense Mode: energy {} -> {}".format(agent, energy, defended))
        energy = defended

    agent.performance = energy
    agent.state = agent.update_state(agent.state, (position, energy, drone.attackPower if drone else None))

    if agent.alive and position == self.target:
      agent.alive = False
      agent.status = 'target reached'
      print("{} reached the rescue target {} with energy {}".format(agent, position, energy))

  def step(self):
    if self.is_done():
      print("There is no one here who could work...")
      return
    actions = []
    for agent in self.agents:
      if agent.alive and not agent.seq:
        agent.alive = False
        agent.status = 'stopped'
        print("{} has no more actions and stops in {}".format(agent, agent.position))
      if agent.alive:
        action = agent.seq.pop(0)
        print("{} decided to do {}.".format(agent, actionName(action)))
        actions.append(action)
      else:
        actions.append(None)
    for (agent, action) in zip(self.agents, actions):
      if action is not None:
        self.execute_action(agent, action)

  def run(self, steps=100):
    super().run(steps)

  def winner(self):
    '''The robots that reached the target with the most energy ([] = no winner, 2 robots = a tie)'''
    finished = [agent for agent in self.agents if agent.status == 'target reached']
    if not finished:
      return []
    best = max(agent.performance for agent in finished)
    return [agent for agent in finished if agent.performance == best]

  def announce_winner(self):
    winners = self.winner()
    if not winners:
      print("No winner: no robot reached the rescue target")
    elif len(winners) > 1:
      print("A tie: {} reached the target with the same energy {}".format(winners, winners[0].performance))
    else:
      print("The winner is {}: it reached the target with energy {}".format(winners[0], winners[0].performance))
    return winners

  def report(self):
    return [agent.report() for agent in self.agents]
