# Lab 4 tasks: pictures of the Hazardous Laboratory
#   plotLabMaze        - the laboratory grid (matplotlib), optionally with the state-space graph and the robots' paths
#   cellNetwork        - the transition model of the single moves (pyvis): ALL available actions are visible
#   stateSpaceNetwork  - the state-space graph: the start, the target, the decision points and the corridors (pyvis)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pyvis.network import Network

from src.mazeData import actions_dict, intTupleTostr
from src.labMazeData import FREE, WALL, DRONE, TARGET, START, actionCosts

cellColors = {
    FREE: '#eef3fb',
    WALL: '#4b4f56',
    DRONE: '#f4a3a3',
    TARGET: '#ffd966',
    START: '#9fd79f',
}
cellLabels = {DRONE: 'drone', TARGET: 'TARGET', START: 'START'}
robotColors = ['#2a78d6', '#eb6834', '#1baf7a']  # UCS - blue, IDDFS - orange (the same color for a robot everywhere)
inkColor = '#52514e'    # labels
mutedColor = '#898781'  # corridors of the graph


def plotLabMaze(maze, title='', graph=None, agents=None, drones=None, planned=False, ax=None):
  '''Draw the laboratory: walls/debris, security drones, the start and the target.
  graph   - a LabGraph: draw its nodes (decision points) and corridors
  agents  - Rescue Robots: draw the path each robot has walked (o = target reached, x = mission failed)
  drones  - the SecurityDrone things of the environment: write their attack power
  planned - draw the robots' planned paths (start -> target) instead of the walked ones'''
  n = maze.shape[0]
  if ax is None:
    fig, ax = plt.subplots(figsize=(6, 6))
  for i in range(n):
    for j in range(n):
      ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=cellColors[int(maze[i, j])], edgecolor='#c3c2b7', linewidth=1))
      if int(maze[i, j]) in cellLabels:
        ax.text(j, i + 0.33, cellLabels[int(maze[i, j])], ha='center', va='center', fontsize=7, color=inkColor)
  for drone in drones or []:
    i, j = drone.location
    ax.text(j, i - 0.3, 'attack {}'.format(drone.attackPower), ha='center', va='center', fontsize=7, color=inkColor)

  if graph is not None:
    for (node, action), moves in graph.corridors.items():
      cells = [node] + graph.cells(node, action)
      ax.plot([c[1] for c in cells], [c[0] for c in cells], color=mutedColor, linewidth=1.2, zorder=2)
    nodes = graph.nodes()
    ax.scatter([c[1] for c in nodes], [c[0] for c in nodes], s=45, color=inkColor, zorder=3, label='node of the state-space graph')

  for k, agent in enumerate(agents or []):
    shift = 0.12 * (k - (len(agents) - 1) / 2)  # a small shift, so that two paths on the same cells stay visible
    color = robotColors[k % len(robotColors)]
    if planned:
      cells = agent.plannedCells()
      label = '{} plan: {} moves, path cost {}'.format(agent.name, len(cells) - 1, agent.solution.path_cost if agent.solution else '-')
      success = agent.solution is not None
    else:
      cells = agent.path
      label = '{} ({}, energy {})'.format(agent.name, agent.status, agent.performance)
      success = agent.status == 'target reached'
    ax.plot([c[1] + shift for c in cells], [c[0] + shift for c in cells], color=color, linewidth=2.5, zorder=4, label=label)
    last = cells[-1]
    ax.scatter([last[1] + shift], [last[0] + shift], s=120, color=color, zorder=5, marker='o' if success else 'X',
               edgecolors='white', linewidths=1.5)

  ax.set_xlim(-0.5, n - 0.5)
  ax.set_ylim(n - 0.5, -0.5)  # row 0 at the top
  ax.set_xticks(range(n))
  ax.set_yticks(range(n))
  ax.xaxis.tick_top()
  ax.set_aspect('equal')
  ax.set_title(title)
  if graph is not None or agents:
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), fontsize=8, ncol=1, frameon=False)
  return ax


def nodeColor(maze, cell):
  return {START: '#4caf50', TARGET: '#ffc107', DRONE: '#e53935'}.get(int(maze[cell]), 'white')


def networkHtml(net):
  '''The HTML page of a pyvis network. When the page opens, the view zooms to show all nodes
  (with the physics off pyvis doesn't do it, and the border nodes may be cut off).'''
  fit = " network.once('afterDrawing', function () { network.fit(); });"
  return net.generate_html().replace("drawGraph();", "drawGraph();" + fit, 1)


def saveNetwork(net, fileName):
  net.write_html(fileName)  # also creates the lib folder with the scripts if it is missing
  with open(fileName, 'w', encoding='utf-8') as f:
    f.write(networkHtml(net))


def cellNetwork(cellTM, maze, fileName='labMazeCells.html', cdn_resources='local'):
  '''The transition model of the single moves as a directed network.
  Every available action is its own curved arrow with its own label,
  so the two directions between two cells don't cover each other: all available actions are visible.
  fileName=None - don't write a file (networkHtml(net) gives the page)'''
  net = Network(directed=True, bgcolor='#242020', font_color='white', height='750px', width='100%', cdn_resources=cdn_resources)
  n = maze.shape[0]
  for i in range(n):
    for j in range(n):
      if maze[i, j] == WALL:
        net.add_node(intTupleTostr((i, j)), label=' ', shape='square', color='#555555', size=12, x=j * 120, y=i * 120,
                     title='{} wall/debris'.format((i, j)))
      else:
        net.add_node(intTupleTostr((i, j)), label=intTupleTostr((i, j)), shape='dot', color=nodeColor(maze, (i, j)),
                     size=10, x=j * 120, y=i * 120, title='{}: actions {}'.format((i, j), list(cellTM[(i, j)])))
  for cell, actions in cellTM.items():
    for action, nextCell in actions.items():
      net.add_edge(intTupleTostr(cell), intTupleTostr(nextCell), label='{}:{}'.format(action, actions_dict[action]),
                   title='{} -> {}: action {} ({}), cost {}'.format(cell, nextCell, action, actions_dict[action], actionCosts[action]),
                   smooth={'type': 'curvedCW', 'roundness': 0.25}, font={'size': 9, 'color': 'white', 'strokeWidth': 0})
  net.toggle_physics(False)
  if fileName:
    saveNetwork(net, fileName)
  return net


def stateSpaceNetwork(graph, maze, fileName='labStateSpace.html', paths=None, sharedColor=robotColors[2], cdn_resources='local'):
  '''The state-space graph: the start, the target and the decision points connected by the corridors.
  Every edge = the direction the robot takes at the node and the cost of the corridor.
  paths - [(corridors of a robot's plan [(node, action), ...], color)]: these edges are drawn thick in the color,
          a corridor on more than one plan in sharedColor
  fileName=None - don't write a file (networkHtml(net) gives the page)'''
  net = Network(directed=True, bgcolor='#242020', font_color='white', height='750px', width='100%', cdn_resources=cdn_resources)
  for node in graph.nodes():
    kind = 'start' if node == graph.start else ('target' if node == graph.target else 'decision point')
    net.add_node(intTupleTostr(node), label=intTupleTostr(node), color=nodeColor(maze, node) if kind != 'decision point' else '#cfd8dc',
                 size=12, x=node[1] * 120, y=node[0] * 120, title='{} {}'.format(node, kind))
  onPath = {}
  for corridors, color in paths or []:
    for corridor in corridors:
      onPath[corridor] = sharedColor if corridor in onPath and onPath[corridor] != color else color
  parallel = {}  # two corridors can connect the same two nodes: each one gets its own curve
  for (node, action), moves in graph.corridors.items():
    nextNode = graph.origin[node][action]
    color = onPath.get((node, action))
    k = parallel[(node, nextNode)] = parallel.get((node, nextNode), -1) + 1
    net.add_edge(intTupleTostr(node), intTupleTostr(nextNode), label='{} ({})'.format(actions_dict[action], graph.cost(node, action)),
                 title='moves {} cost {}'.format(moves, graph.cost(node, action)), color=color or '#8a8a8a', width=5 if color else 1,
                 smooth={'type': 'curvedCW', 'roundness': 0.25 + 0.35 * k}, font={'size': 9, 'color': 'white', 'strokeWidth': 0})
  net.toggle_physics(False)
  if fileName:
    saveNetwork(net, fileName)
  return net
