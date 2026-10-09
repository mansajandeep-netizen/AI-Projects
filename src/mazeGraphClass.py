from src.graphClass import Graph

# The 4 directions in clockwise order.
# Turning 'right' = the next direction in this list, turning 'left' = the previous one.
headings = ['N', 'E', 'S', 'W']


def turn(heading, action):
  '''Return the new heading after a 90 degree turn.
  Example: turn('N', 'right') -> 'E',  turn('N', 'left') -> 'W' '''
  i = headings.index(heading)
  if action == 'right':
    return headings[(i + 1) % 4]  # % 4 wraps around: after 'W' comes 'N' again
  return headings[(i - 1) % 4]


class MazeGraph(Graph):
  '''The maze as a graph (the state space).
  It is the course Graph class + the (column, row) location of every node.
  All corridors are horizontal or vertical, so from two locations we know the
  direction (N/E/S/W) of a corridor. The Agent needs it for the actions advance / left / right.'''

  def __init__(self, graph_dict=None, locations=None):
    super().__init__(graph_dict)
    self.locations = locations or {}

  def getLocation(self, a):
    return self.locations.get(a)

  def direction(self, a, b):
    '''The direction of the corridor that goes from node a to node b.'''
    ax, ay = self.locations[a]
    bx, by = self.locations[b]

    if ax == bx:  # same column -> the corridor is vertical (y grows to the South)
      if by > ay:
        return 'S'
      return 'N'

    # same row -> the corridor is horizontal (x grows to the East)
    if bx > ax:
      return 'E'
    return 'W'

  def neighbor(self, a, heading):
    '''The node in front of the Agent when it stands at node a looking to `heading`.
    Returns None when there is a wall in that direction.'''
    for b in self.get(a):
      if self.direction(a, b) == heading:
        return b
    return None
