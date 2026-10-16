#How do we decide which node from the frontier to expand next?
from src.nodeClass import Node
from queue import PriorityQueue
import itertools

nodeColors={
    "start":"red",
    "goal": "green",
    "frontier": "orange",
    "expanded":"pink"
}

def BestFirstSearchAgentProgram(f=None):
  #with BFS we choose a node, n, with minimum value of some evaluation function, f (n).
    
    def program(problem):

      node = Node(problem.initial)
      #node.color=nodeColors["start"]
      #print(node.state)
      frontier = PriorityQueue()
      frontier.put((1,node))
      #node.color=nodeColors["frontier"]
      reached = {problem.initial:node}

      while frontier:
        node = frontier.get()[1]
        #node.color=nodeColors["expanded"]
        print(node)

        if problem.goal_test(node.state):
          node.color=nodeColors["goal"]
          return node

        #reached.add(node.state)
        for child in node.expand(problem):
            if child.state not in reached or child.path_cost<reached[child.state].path_cost:
                frontier.put((1,child))
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


# =====================================================================
# Lab 4 tasks: Uniform-Cost Search and Iterative Deepening (Iterative DLS)
# =====================================================================

def expand(problem, node):
    '''EXPAND(problem, node) yields the child nodes (see the BEST-FIRST-SEARCH pseudo-code)'''
    s = node.state
    for action in problem.actions(s):
        s1 = problem.result(s, action)
        cost = problem.path_cost(node.path_cost, s, action, s1)
        yield Node(s1, node, action, cost)


def BestFirstSearch(problem, f, stats=None):
    '''BEST-FIRST-SEARCH(problem, f) returns a solution node or failure (None).
    The frontier is a priority queue ordered by the evaluation function f(n).'''
    counter = itertools.count()  # nodes with the same f(n) leave the frontier in the order they came (FIFO)
    node = Node(problem.initial)
    frontier = PriorityQueue()
    frontier.put((f(node), next(counter), node))
    reached = {problem.initial: node}

    while not frontier.empty():
        node = frontier.get()[2]
        if problem.goal_test(node.state):
            return node
        if stats is not None:
            stats['expanded'] += 1
        for child in expand(problem, node):
            s = child.state
            if s not in reached or child.path_cost < reached[s].path_cost:
                reached[s] = child
                frontier.put((f(child), next(counter), child))

    return None  # failure: the frontier is empty, there is no solution


def UniformCostSearchAgentProgram():
    '''Uniform-Cost Search: Best-First Search with the evaluation function f(n) = g(n) = PATH-COST,
    the total cost of the path from the initial state to the node n.'''

    def program(problem):
        program.stats = {'expanded': 0}
        node = BestFirstSearch(problem, lambda n: n.path_cost, program.stats)
        print("UCS: {} nodes expanded, {}".format(program.stats['expanded'],
              "path cost = {}".format(node.path_cost) if node else "no solution"))
        return node

    return program


cutoff = 'cutoff'  # DLS result: the depth limit stopped the search, a deeper search may find a solution
failure = None     # DLS result: there is no solution


def isCycle(node):
    '''True if the state of the node is already on the path from the root to the node'''
    ancestor = node.parent
    while ancestor is not None:
        if ancestor.state == node.state:
            return True
        ancestor = ancestor.parent
    return False


def DepthLimitedSearch(problem, limit, stats=None):
    '''DEPTH-LIMITED-SEARCH(problem, limit) returns a solution node, failure or cutoff'''
    return RecursiveDLS(Node(problem.initial), problem, limit, stats)


def RecursiveDLS(node, problem, limit, stats=None):
    '''RECURSIVE-DLS(node, problem, limit) returns a solution node, failure or cutoff'''
    if stats is not None:
        stats['visited'] += 1
    cutoff_occurred = False
    if problem.goal_test(node.state):
        return node
    elif node.depth == limit:
        return cutoff
    else:
        for successor in expand(problem, node):
            # the laboratory graph has cycles: never go back to a state that is already on this path
            # (without this check DLS would always find a longer path around a cycle and never return failure)
            if isCycle(successor):
                continue
            result = RecursiveDLS(successor, problem, limit, stats)
            if result is cutoff:
                cutoff_occurred = True
            elif result is not failure:
                return result
    return cutoff if cutoff_occurred else failure


def IDSearchAgentProgram():
    '''Iterative Deepening Search (Iterative DLS): DLS with the depth limit 0, 1, 2, 3, ...
    Every iteration starts again from the initial state.
    It stops when the target is found (a solution node) or when DLS returns failure:
    no cutoff happened, so all paths were searched and no solution exists.'''

    def program(problem):
        program.iterations = []  # (depth limit, result, nodes visited) of every DLS
        for depth in itertools.count():  # for depth = 0 to infinity
            stats = {'visited': 0}
            result = DepthLimitedSearch(problem, depth, stats)
            outcome = 'cutoff' if result is cutoff else ('failure' if result is failure else 'solution')
            program.iterations.append((depth, outcome, stats['visited']))
            print("IDS: depth limit = {}: {} ({} nodes visited)".format(depth, outcome, stats['visited']))
            if result is not cutoff:
                return result

    return program
