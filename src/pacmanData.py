'''PacMan World: maze generator, graph builder and drawing helpers.

Maze encoding (same as the tutorial):  0 = wall,  1 = open path,  2 = food
'''
import random
from collections import deque
from itertools import permutations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from src.mazeData import (defineMazeAvailableActions, makeMazeTransformationModel,
                          mazeStatesLocations, intTupleTostr)
from src.maze2025GraphClass import mazeGraph

WALL, PATH, FOOD = 0, 1, 2

# colours for the legs of a route (fixed order: leg 1 is always blue, leg 2 orange, ...)
SEGMENT_COLORS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100',
                  '#e87ba4', '#008300', '#6250d6', '#e34948']
INK, INK_2, MUTED = '#0b0b0b', '#52514e', '#898781'
SURFACE, GRID, WALL_COLOR = '#fcfcfb', '#e1e0d9', '#383835'
GHOST_COLOR = '#d03b3b'


# ---------------------------------------------------------------------------
# Building the world
# ---------------------------------------------------------------------------
def reachableCells(maze, start):
    '''All open cells that can be reached from `start` (breadth-first flood fill).'''
    n = maze.shape[0]
    seen, queue = {start}, deque([start])
    while queue:
        r, c = queue.popleft()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < n and 0 <= nc < n and maze[nr, nc] != WALL and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc))
    return seen


def makePacmanMaze(n=10, wall_ratio=0.2, food_ratio=0.05, start=None, exit=None, seed=None, max_tries=1000):
    '''Random PacMan World.

    * exactly round(wall_ratio * n*n) walls
    * exactly round(food_ratio * n*n) Fixed Food Dots (5% of the space),
      placed at random - the start and the exit cells may also get food
    * start / exit are random open cells unless given
    * the world is only accepted if the exit and every food dot can be reached
      from the start (otherwise the task would be impossible)

    returns  maze (numpy array), start, exit, foods (list of cells)
    '''
    rng = random.Random(seed)
    cells = [(i, j) for i in range(n) for j in range(n)]
    n_walls = round(wall_ratio * n * n)
    n_food = max(1, round(food_ratio * n * n))
    fixed = {c for c in (start, exit) if c is not None}

    for _ in range(max_tries):
        maze = np.ones((n, n), dtype=int)
        for c in rng.sample([c for c in cells if c not in fixed], n_walls):
            maze[c] = WALL
        open_cells = [c for c in cells if maze[c] != WALL]
        s = start if start is not None else rng.choice(open_cells)
        e = exit if exit is not None else rng.choice([c for c in open_cells if c != s])
        reach = reachableCells(maze, s)
        if e not in reach or len(reach) < n_food:
            continue
        foods = rng.sample(sorted(reach), n_food)  # random order = the "listed" order used in Task 2
        for c in foods:
            maze[c] = FOOD
        return maze, s, e, foods
    raise RuntimeError("Could not build a solvable maze - try fewer walls.")


def buildPacmanGraph(maze):
    '''maze array -> available actions -> transition model -> mazeGraph (same steps as the tutorial).'''
    acts = defineMazeAvailableActions(maze)
    tm = makeMazeTransformationModel(acts)
    return mazeGraph(tm, mazeStatesLocations(list(tm.keys())))


def foodCells(maze):
    return [tuple(int(v) for v in c) for c in np.argwhere(maze == FOOD)]


# ---------------------------------------------------------------------------
# Exact costs (Uniform-Cost Search) - used to check the heuristics
# ---------------------------------------------------------------------------
def exactCostsFrom(graph, source):
    '''Cheapest path cost from `source` to every reachable cell (Dijkstra / UCS).'''
    import heapq
    dist = {source: 0}
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph.get(u).items():
            if d + w < dist.get(v, float('inf')):
                dist[v] = d + w
                heapq.heappush(pq, (d + w, v))
    return dist


def bestFoodOrder(graph, start, exit, foods):
    '''Brute force over every visiting order (5 foods -> 120 orders).
    returns (lowest total cost, order). Used only to judge the greedy strategy.'''
    pts = [start] + list(foods) + [exit]
    cost = {p: exactCostsFrom(graph, p) for p in pts}
    best = (float('inf'), None)
    for order in permutations(foods):
        route = [start, *order, exit]
        total = sum(cost[a][b] for a, b in zip(route, route[1:]))
        best = min(best, (total, list(order)))
    return best


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _label(ax, cell, text, face, color, size=9):
    ax.text(cell[1] + 0.5, cell[0] + 0.5, text, ha='center', va='center', fontsize=size,
            fontweight='bold', color=color, zorder=6,
            bbox=dict(boxstyle='round,pad=0.25', fc=face, ec=INK, lw=0.8))


def drawPacmanWorld(maze, start, exit, foods=None, ghosts=None, segments=None,
                    title=None, ax=None, food_order=None, show_legend=True):
    '''Draw the maze as a grid.

    foods     - list of food cells (default: cells with value 2)
    ghosts    - list of (cell, power) to show the hidden ghosts ("god view")
    segments  - list of dicts {'path': [cells], 'label': str}; each leg of the route
                gets its own colour (start->goal1, goal1->goal2, ...)
    food_order- optional {cell: k} to print the visiting order next to each food dot
    '''
    n = maze.shape[0]
    foods = foodCells(maze) if foods is None else foods
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(8, 6.5), layout='constrained')
    ax.set_facecolor(SURFACE)

    for i in range(n):
        for j in range(n):
            if maze[i, j] == WALL:
                ax.add_patch(Rectangle((j, i), 1, 1, fc=WALL_COLOR, ec=SURFACE, lw=1, zorder=1))
    for k in range(n + 1):
        ax.plot([0, n], [k, k], color=GRID, lw=0.8, zorder=0)
        ax.plot([k, k], [0, n], color=GRID, lw=0.8, zorder=0)

    handles = []
    segments = segments or []
    m = len(segments)
    for k, seg in enumerate(segments):
        color = SEGMENT_COLORS[k] if m <= len(SEGMENT_COLORS) else plt.cm.Blues(0.35 + 0.6 * k / max(1, m - 1))
        off = (k - (m - 1) / 2) * 0.09 if m > 1 else 0.0  # small shift so overlapping legs stay visible
        path = seg['path']
        xs = [c[1] + 0.5 + off for c in path]
        ys = [c[0] + 0.5 + off for c in path]
        ax.plot(xs, ys, color=color, lw=2.4, solid_capstyle='round', zorder=3)
        for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):  # small arrow on each move
            ax.annotate('', xy=(x0 + 0.62 * (x1 - x0), y0 + 0.62 * (y1 - y0)),
                        xytext=(x0 + 0.38 * (x1 - x0), y0 + 0.38 * (y1 - y0)),
                        arrowprops=dict(arrowstyle='-|>', color=color, lw=1.2, mutation_scale=10), zorder=3)
        handles.append(Line2D([0], [0], color=color, lw=2.4, label=seg.get('label', f'leg {k + 1}')))

    for f in foods:
        ax.plot(f[1] + 0.5, f[0] + 0.5, 'o', ms=11, mfc='#fab219', mec=INK, mew=1.0, zorder=5)
        if food_order and f in food_order:
            ax.text(f[1] + 0.86, f[0] + 0.2, str(food_order[f]), fontsize=8, color=INK,
                    ha='center', va='center', zorder=6, fontweight='bold')
    for cell, power in (ghosts or []):
        _label(ax, cell, f'G{power}', GHOST_COLOR, 'white', size=8)
    _label(ax, start, 'S', 'white', INK)
    _label(ax, exit, 'E', '#d9f2d9', INK)

    ax.set_xlim(0, n)
    ax.set_ylim(n, 0)
    ax.set_xticks([k + 0.5 for k in range(n)])
    ax.set_xticklabels(range(n), fontsize=8, color=MUTED)
    ax.set_yticks([k + 0.5 for k in range(n)])
    ax.set_yticklabels(range(n), fontsize=8, color=MUTED)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.set_aspect('equal')
    if title:
        ax.set_title(title, fontsize=11, color=INK, loc='left')

    if show_legend:
        handles += [Line2D([0], [0], marker='o', ls='', ms=9, mfc='#fab219', mec=INK, label='food dot'),
                    Rectangle((0, 0), 1, 1, fc=WALL_COLOR, label='wall'),
                    Line2D([0], [0], marker='s', ls='', ms=9, mfc='white', mec=INK, label='S = start, E = exit')]
        if ghosts:
            handles.append(Line2D([0], [0], marker='s', ls='', ms=9, mfc=GHOST_COLOR, mec=INK,
                                  label='G<power> = ghost'))
        ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(1.01, 1), frameon=False, fontsize=8.5)
    if own_fig:
        plt.show()
    return ax


def pacmanPyvis(graph, maze, start, exit, segments=None, filename='PacmanWorld_route.html',
                heading='PacMan World - route', cdn_resources='local', height='750px'):
    '''Same PyVis picture as in the tutorial, but the edges of each leg of the
    route get the leg colour. Writes an HTML file (open it in a browser).
    filename=None returns the HTML text instead (the web app uses cdn_resources='remote').'''
    from pyvis.network import Network
    net = Network(heading=heading, bgcolor='#242020', font_color='white',
                  height=height, width='100%', directed=True, cdn_resources=cdn_resources)
    colors = {'wall': 'red', 'path': 'white', 'food': 'yellow', 'goal': 'green', 'init': 'gold'}
    cells = list(graph.origin.keys())
    ids = [intTupleTostr(c) for c in cells]
    node_colors = []
    for c in cells:
        if c == exit:
            node_colors.append(colors['goal'])
        elif c == start:
            node_colors.append(colors['init'])
        else:
            node_colors.append({WALL: colors['wall'], PATH: colors['path'], FOOD: colors['food']}[int(maze[c])])
    xs = [graph.getLocation(c)[0] for c in cells]
    ys = [graph.getLocation(c)[1] for c in cells]
    net.add_nodes(ids, color=node_colors, x=xs, y=ys, size=[10] * len(ids), title=ids, label=[''] * len(ids))

    leg_of = {}
    for k, seg in enumerate(segments or []):
        for a, b in zip(seg['path'], seg['path'][1:]):
            leg_of.setdefault((a, b), k)
    for a in graph.nodes():
        for b in graph.get(a):
            if (a, b) in leg_of:
                k = leg_of[(a, b)]
                net.add_edge(intTupleTostr(a), intTupleTostr(b), color=SEGMENT_COLORS[k % 8], width=4,
                             title=f'leg {k + 1}')
            else:
                net.add_edge(intTupleTostr(a), intTupleTostr(b), color='#5a5a5a', width=1)
    net.toggle_physics(False)
    if filename is None:
        return net.generate_html(notebook=False)
    net.write_html(filename, notebook=False, open_browser=False)
    return filename


def plotPerformance(agents, title='Performance during the run', log=True):
    '''Line chart of each agent's performance after every move (Tasks 5-6).
    Markers: circle = food eaten (x2), cross = ghost beaten (-10%), X = killed.
    Agents with identical runs are drawn as one line.'''
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
    groups = []
    for k, a in enumerate(agents):
        key = tuple((h[0], h[2]) for h in a.history)
        for g in groups:
            if g['key'] == key:
                g['names'].append(a.name)
                break
        else:
            groups.append({'key': key, 'names': [a.name], 'agent': a, 'color': SEGMENT_COLORS[k]})

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.set_facecolor(SURFACE)
    for g in groups:
        a, color = g['agent'], g['color']
        short = [nm.replace('Pac-Man (', '').rstrip(')') if nm.startswith('Pac-Man (') else nm for nm in g['names']]
        label = ' = '.join(g['names']) + (' (identical runs)' if len(g['names']) > 1 else '')
        t = [h[0] for h in a.history]
        p = [h[2] for h in a.history]
        ax.plot(t, p, color=color, lw=2, label=label, zorder=3)
        ax.text(t[-1] + 0.6, p[-1], f"{' = '.join(short)}: {p[-1]:g}", color=INK_2, fontsize=8.5, va='center')
        for (time, kind, loc, perf) in a.events:
            if kind == 'food':
                ax.plot(time, perf, 'o', ms=8, mfc=color, mec=SURFACE, mew=2, zorder=4)
            elif kind == 'won':
                ax.plot(time, perf, 'X', ms=9, mfc=color, mec=SURFACE, mew=1.5, zorder=4)
            elif kind == 'killed':
                ax.plot(time, perf, 'X', ms=14, mfc=GHOST_COLOR, mec=INK, zorder=5)
    if log:
        ax.set_yscale('log')
        values = [h[2] for a in agents for h in a.history]
        ticks = [v for v in (5, 10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120)
                 if min(values) * 0.7 <= v <= max(values) * 1.4]
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
        ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(axis='y', color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color('#c3c2b7')
    ax.tick_params(colors=MUTED, labelsize=8.5)
    ax.tick_params(axis='y', which='minor', length=0)
    ax.set_xlabel('time step (moves made)', color=INK_2, fontsize=9)
    ax.set_ylabel('performance' + (' (log scale)' if log else ''), color=INK_2, fontsize=9)
    ax.set_title(title, loc='left', color=INK, fontsize=11)
    marks = [Line2D([0], [0], marker='o', ls='', ms=8, mfc=MUTED, mec=SURFACE, label='ate food (x2)'),
             Line2D([0], [0], marker='X', ls='', ms=9, mfc=MUTED, mec=SURFACE, label='beat a ghost (-10%)')]
    if any(e[1] == 'killed' for a in agents for e in a.events):
        marks.append(Line2D([0], [0], marker='X', ls='', ms=12, mfc=GHOST_COLOR, mec=INK, label='killed by a ghost'))
    handles, _ = ax.get_legend_handles_labels()
    ax.legend(handles=handles + marks, loc='upper left', frameon=False, fontsize=8.5)
    xmax = max(a.history[-1][0] for a in agents)
    ax.set_xlim(0, xmax * 1.25 + 1)
    plt.tight_layout()
    plt.show()
