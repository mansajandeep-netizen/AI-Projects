#How do we decide which node from the frontier to expand next?
from src.nodeClass import Node
from src.heuristics import manhattanDistance
from queue import PriorityQueue

import itertools
import math
import sys

sys.setrecursionlimit(10000)  # IDA* and RBFS are recursive

nodeColors={
    "start":"red",
    "goal": "green",
    "frontier": "orange",
    "expanded":"pink"
}

INF = (math.inf, math.inf)


def _hname(h):
  return getattr(h, '__name__', str(h))


def _report(stats):
  '''Task 1: print the number of expanded nodes and the total cost of the path.'''
  if stats.get('goal') is None:
    print(f"[{stats['algorithm']} | h={stats['heuristic']}] no path found "
          f"| nodes expanded: {stats['nodes_expanded']}")
  else:
    extra = f" | iterations: {stats['iterations']}" if 'iterations' in stats else ""
    print(f"[{stats['algorithm']} | h={stats['heuristic']}] goal {stats['goal']} reached "
          f"| nodes expanded: {stats['nodes_expanded']} | path cost: {stats['path_cost']} "
          f"| steps: {stats['steps']}{extra}")


def _steps_estimate(node, goal, tie_break):
  '''Second part of f used only to break ties: moves made so far + at least the
  Manhattan distance still to go. Cost always comes first; among paths with the same
  cost the one with fewer moves wins (every move costs Pac-Man 1 performance point).'''
  return node.depth + manhattanDistance(node.state, goal) if tie_break else 0


# ---------------------------------------------------------------------------
# Task 1 (+ Task 2): refined A*
# ---------------------------------------------------------------------------
def A_StarSearchAgentProgram(f=None, verbose=True, report=True, tie_break=True):
    '''A* search:  f(n) = g(n) + h(n).

    f         - the heuristic h(state, goal). Default: Euclidean distance (math.dist).
    verbose   - print the frontier trace (like the tutorial).
    report    - print the summary line (Task 1).
    tie_break - on equal f, prefer the path with fewer moves.

    Refinements compared with the tutorial version:
      * counts the nodes expanded and reports the total path cost (Task 1);
        the numbers are also kept in program.stats
      * uses the heuristic passed in for the start node too (it was hard-coded to math.dist)
      * stops when the frontier is empty (the old `while frontier:` waited forever
        when the goal could not be reached)
      * skips old frontier entries that were replaced by a cheaper path
    '''
    if f is None:
      f = math.dist

    def program(problem):
      stats = {'algorithm': 'A*', 'heuristic': _hname(f), 'nodes_expanded': 0,
               'nodes_generated': 1, 'max_frontier': 1, 'peak_memory': 1,
               'path_cost': None, 'steps': None, 'goal': None}
      program.stats = stats
      if verbose:
        print("Hi")

      def entry(n):
        return (n.path_cost + round(f(n.state, problem.goal), 3),
                _steps_estimate(n, problem.goal, tie_break), next(counter), n)

      node = Node(problem.initial)
      counter = itertools.count()  # last tie-breaker, so the queue never has to compare Nodes
      frontier = PriorityQueue()
      frontier.put(entry(node))
      reached = {problem.initial: node}

      while not frontier.empty():
        if verbose:
          print([(e[0], e[3]) for e in frontier.queue])
        node = frontier.get()[3]
        if reached[node.state] is not node:  # a better path to this state was found later
          continue
        if verbose:
          print("The node {} is extracted from frontier:".format(node.state))

        if problem.goal_test(node.state):
          stats.update(path_cost=node.path_cost, steps=node.depth, goal=node.state)
          if verbose:
            print("We have found our goal: {}".format(node.state))
          if report:
            _report(stats)
          return node

        stats['nodes_expanded'] += 1
        for child in node.expand(problem):
            stats['nodes_generated'] += 1
            old = reached.get(child.state)
            if old is None or (child.path_cost, child.depth) < (old.path_cost, old.depth):
                if verbose:
                  print("The child node {}.".format(child))
                frontier.put(entry(child))
                reached[child.state] = child
        stats['max_frontier'] = max(stats['max_frontier'], frontier.qsize())
        stats['peak_memory'] = len(reached)  # A* keeps every node it has reached

      if report:
        _report(stats)
      return None

    program.stats = {}
    return program


# ---------------------------------------------------------------------------
# Task 7: Iterative-Deepening A* (IDA*)
# ---------------------------------------------------------------------------
def IDA_StarSearchAgentProgram(h=None, verbose=False, report=True, tie_break=False):
    '''IDA*: repeated depth-first searches, each limited by an f-cost "contour".

    function IDA*(problem)
        root    <- MAKE-NODE(INITIAL-STATE[problem]);  f-limit <- f(root)
        loop:
            solution, f-limit <- DFS-CONTOUR(root, f-limit)
            if solution is non-null  return solution
            if f-limit = infinity    return failure

    DFS-CONTOUR(node, f-limit) cuts off every node with f > f-limit and returns the
    smallest f that was cut off - that becomes the next, larger f-limit.

    Notes
      * Memory: only the current path is stored (no frontier, no reached table).
        A state that is already on the current path is skipped - otherwise the
        free left/right moves (cost 0) would let the search walk in circles forever.
      * f-values are stored as pairs (g + h, tie-break part). With the default
        tie_break=False the second part is always 0, so this is exactly the
        textbook IDA*. tie_break=True also prefers fewer moves among equally cheap
        paths, but it can be VERY slow here: the free left/right moves create a huge
        number of equally cheap paths and IDA* has no memory of visited cells.
    '''
    if h is None:
      h = math.dist

    def program(problem):
      stats = {'algorithm': 'IDA*', 'heuristic': _hname(h), 'nodes_expanded': 0,
               'nodes_generated': 1, 'iterations': 0, 'max_depth': 0, 'peak_memory': 1,
               'path_cost': None, 'steps': None, 'goal': None}
      program.stats = stats

      def fcost(node):
        return (node.path_cost + h(node.state, problem.goal),
                _steps_estimate(node, problem.goal, tie_break))

      root = Node(problem.initial)
      on_path = {root.state}
      live = [1]

      def dfs_contour(node, f_limit):
        f_node = fcost(node)
        if f_node > f_limit:
          return None, f_node
        if problem.goal_test(node.state):
          return node, f_limit
        stats['nodes_expanded'] += 1
        stats['max_depth'] = max(stats['max_depth'], node.depth)
        next_f = INF
        # try the most promising child first
        children = sorted((s for s in node.expand(problem) if s.state not in on_path), key=fcost)
        live[0] += len(children)  # nodes held in memory right now
        stats['peak_memory'] = max(stats['peak_memory'], live[0])
        for s in children:
          stats['nodes_generated'] += 1
          on_path.add(s.state)
          solution, new_f = dfs_contour(s, f_limit)
          on_path.discard(s.state)
          if solution is not None:
            return solution, f_limit
          next_f = min(next_f, new_f)
        live[0] -= len(children)
        return None, next_f

      f_limit = fcost(root)
      while True:
        stats['iterations'] += 1
        if verbose:
          print(f"IDA* iteration {stats['iterations']}: f-limit = {round(f_limit[0], 3)}")
        solution, f_limit = dfs_contour(root, f_limit)
        if solution is not None:
          stats.update(path_cost=solution.path_cost, steps=solution.depth, goal=solution.state)
          if report:
            _report(stats)
          return solution
        if f_limit[0] == math.inf:
          if report:
            _report(stats)
          return None

    program.stats = {}
    return program


# ---------------------------------------------------------------------------
# Task 8: Recursive Best-First Search (RBFS)
# ---------------------------------------------------------------------------
def RBFSAgentProgram(h=None, verbose=False, report=True, tie_break=False):
    '''RBFS: best-first search that uses only linear memory.

    function RBFS(problem, node, f_limit)
        if node is a goal: return node
        successors <- EXPAND(node);  if empty: return failure, infinity
        for each s: s.f <- max(g(s) + h(s), node.f)
        loop:
            best <- successor with the lowest f
            if best.f > f_limit: return failure, best.f
            alternative <- second-lowest f among successors
            result, best.f <- RBFS(problem, best, min(f_limit, alternative))
            if result != failure: return result

    The search follows the best path until its f-value grows above the best
    alternative somewhere higher up; it then "unwinds" and remembers the backed-up
    f-value of the forgotten subtree, so it can come back to it later.
    As in IDA*: states already on the current path are skipped (no cycles), and
    f-values are pairs (g + h, tie-break part); with the default tie_break=False the
    second part is 0, i.e. the textbook RBFS.
    '''
    if h is None:
      h = math.dist

    def program(problem):
      stats = {'algorithm': 'RBFS', 'heuristic': _hname(h), 'nodes_expanded': 0,
               'nodes_generated': 1, 'max_depth': 0, 'peak_memory': 1,
               'path_cost': None, 'steps': None, 'goal': None}
      program.stats = stats

      def fcost(node):
        return (node.path_cost + h(node.state, problem.goal),
                _steps_estimate(node, problem.goal, tie_break))

      root = Node(problem.initial)
      root.f = fcost(root)
      on_path = {root.state}
      live = [1]

      def rbfs(node, f_limit):
        if problem.goal_test(node.state):
          return node, node.f
        stats['nodes_expanded'] += 1
        stats['max_depth'] = max(stats['max_depth'], node.depth)
        successors = [s for s in node.expand(problem) if s.state not in on_path]
        if not successors:
          return None, INF
        for s in successors:
          stats['nodes_generated'] += 1
          s.f = max(fcost(s), node.f)
        live[0] += len(successors)  # nodes held in memory right now
        stats['peak_memory'] = max(stats['peak_memory'], live[0])
        while True:
          successors.sort(key=lambda s: s.f)
          best = successors[0]
          if best.f[0] == math.inf or best.f > f_limit:
            result, f_back = None, best.f            # failure, best.f
            break
          alternative = successors[1].f if len(successors) > 1 else INF
          if verbose:
            print(f"RBFS: go to {best.state} (f={round(best.f[0], 3)}), "
                  f"limit={round(min(f_limit, alternative)[0], 3)}")
          on_path.add(best.state)
          result, best.f = rbfs(best, min(f_limit, alternative))
          on_path.discard(best.state)
          if result is not None:
            f_back = best.f                          # result, best.f
            break
        live[0] -= len(successors)  # this level's successors are forgotten again
        return result, f_back

      solution, _ = rbfs(root, INF)
      if solution is not None:
        stats.update(path_cost=solution.path_cost, steps=solution.depth, goal=solution.state)
      if report:
        _report(stats)
      return solution

    program.stats = {}
    return program





def BestFirstSearchAgentProgram(f=None):
  #with BFS we choose a node, n, with minimum value of some evaluation function, f (n).
    
    def program(problem):

      node = Node(problem.initial)
      #node.color=nodeColors["start"]
      #print(node.state)
      frontier = PriorityQueue()
      frontier.put((1,node))
      print(f"The {node} is being pushed to frontier ...")
      #node.color=nodeColors["frontier"]
      reached = {problem.initial:node}

      while frontier:
        node = frontier.get()[1]
        #node.color=nodeColors["expanded"]
        print(f"The {node} is being extracted from frontier ...")

        if problem.goal_test(node.state):
          node.color=nodeColors["goal"]
          print(f"We have found our goal:  {node}!")
          return node

        #reached.add(node.state)
        for child in node.expand(problem):
            if child.state not in reached or child.path_cost<reached[child.state].path_cost:
                frontier.put((1,child))
                print(f"The child {child} is being pushed to frontier ...")
                #child.color=nodeColors["frontier"]
                reached.update({child.state:child})
            
        #node.color=nodeColors["expanded"]
      return None

    return program
  
 

def BestFirstSearchAgentProgramForShow(f=None):
  #with BFS we choose a node, n, with minimum value of some evaluation function, f (n).
    
    def program(problem):
      #print(111)
      steps = 0
      allNodeColors = []
      nodeColors = {k : 'white' for k in problem.graph.nodes()}

      node = Node(problem.initial)
      nodeColors[node.state] = "yellow"
      steps += 1
      allNodeColors.append(dict(nodeColors))

      #print(node.state)
      frontier = PriorityQueue()
      frontier.put((1,node))

      nodeColors[node.state] = "orange"
      steps += 1
      allNodeColors.append(dict(nodeColors))



      reached = {problem.initial:node}

      while frontier:
        node = frontier.get()[1]
        nodeColors[node.state] = "red"
        steps += 1
        allNodeColors.append(dict(nodeColors))
        #print(node)

        if problem.goal_test(node.state):
          nodeColors[node.state] = "green"
          steps += 1
          allNodeColors.append(dict(nodeColors))
          return (node,steps,allNodeColors)
          

        #reached.add(node.state)
        for child in node.expand(problem):
            if child.state not in reached or child.path_cost<reached[child.state].path_cost:
                frontier.put((1,child))
                nodeColors[child.state] = "orange"
                steps += 1
                allNodeColors.append(dict(nodeColors))

                reached.update({child.state:child})

        # modify the color of explored nodes to blue
        nodeColors[node.state] = "blue"
        steps += 1
        allNodeColors.append(dict(nodeColors))
            
      return None

    return program