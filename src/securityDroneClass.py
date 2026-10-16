import random

from src.thingClass import Thing


class SecurityDrone(Thing):
  '''A security drone (an enemy) that guards one cell of the laboratory.
  Its attack power is random: 10%-40% of the number of nodes in the state-space graph.'''

  def __init__(self, nodesCount, rng=random):
    self.attackPower = round(rng.uniform(0.1 * nodesCount, 0.4 * nodesCount), 1)
    self.location = None

  def __repr__(self):
    return '<SecurityDrone attack={} in {}>'.format(self.attackPower, self.location)
