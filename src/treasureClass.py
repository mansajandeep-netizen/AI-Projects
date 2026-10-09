from src.thingClass import Thing
from data.treasureMazeData import treasureTypes

class Treasure(Thing):
  '''A treasure lying at a node of the maze: Gold, Diamond, Pizza or ExtraPoints'''

  def __init__(self, name):
    self.name = name
    self.icon, self.description = treasureTypes[name]
    self.location = None

  def __repr__(self):
    #no icon here: a Windows console can't print emoji
    return self.description
