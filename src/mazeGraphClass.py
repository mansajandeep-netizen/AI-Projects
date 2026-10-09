from src.graphClass import Graph

headings = ['N', 'E', 'S', 'W'] # clockwise: 'right' takes the next heading, 'left' takes the previous one

def turn(heading, action):
  #the new heading after the 'left' or 'right' action (a 90 degrees turn)
  i = headings.index(heading)
  return headings[(i + 1) % 4] if action == 'right' else headings[(i - 1) % 4]


class MazeGraph(Graph):
  '''The state space of the maze: an undirected Graph + a 2D location of every node.
  All corridors are horizontal or vertical, so the locations tell the direction (N/E/S/W) of every corridor:
  the Agent needs it for the relative actions advance / left / right.'''

  def __init__(self, graph_dict=None, locations=None):
    super().__init__(graph_dict)
    self.locations = locations or {}

  def getLocation(self, a):
    return self.locations.get(a)

  def direction(self, a, b):
    #the direction of the corridor from node a to node b
    (ax, ay), (bx, by) = self.locations[a], self.locations[b]
    if ax == bx:
      return 'S' if by > ay else 'N'
    return 'E' if bx > ax else 'W'

  def neighbor(self, a, heading):
    #the node reached by going from node a in the given direction (None = a wall)
    for b in self.get(a):
      if self.direction(a, b) == heading:
        return b
    return None
