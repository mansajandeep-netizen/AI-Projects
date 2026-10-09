#How do we decide which node from the frontier to expand next?
from src.nodeClass import Node
from queue import PriorityQueue
from collections import deque

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


def BreadthFirstSearchAgentProgram():
  #Uninformed search: we always expand the shallowest node of the frontier (FIFO queue).
  #All actions cost 1, so the first solution found has the fewest actions.

    def program(problem):

      node = Node(problem.initial)
      if problem.goal_test(node.state):
        return node

      frontier = deque([node]) #FIFO queue
      reached = {problem.initial}

      while frontier:
        node = frontier.popleft()

        for child in node.expand(problem):
            if problem.goal_test(child.state): #early goal test
              return child
            if child.state not in reached:
              reached.add(child.state)
              frontier.append(child)

      return None #failure: the frontier is empty, there is no solution

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