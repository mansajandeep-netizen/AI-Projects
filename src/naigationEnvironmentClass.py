from src.environmentProClass import environmentPro
from src.problemSolvingAgentProgramClass import SimpleProblemSolvingAgentProgram

class NavigationEnvironment(environmentPro):
  '''The map (graph) where a Problem-Solving Agent moves from a city to a neighbouring city.'''

  def __init__(self, graph):
    super().__init__()
    self.status = graph #the state space

  def add_thing(self, thing, location=None):
    if isinstance(thing, SimpleProblemSolvingAgentProgram):
      if thing in self.agents:
        print("Can't add the same agent twice")
        return
      thing.location = thing.state
      self.agents.append(thing)
      thing(self.percept(thing)) #the Agent formulates its goal(s) and the problem, then searches for a solution
      print("The Agent in {} with performance {}".format(thing.state, thing.performance))
    else:
      super().add_thing(thing, location)

  def percept(self, agent):
    return agent.state

  def is_done(self):
    return not any(agent.alive for agent in self.agents)

  def execute_action(self, agent, action):
    if not self.is_agent_alive(agent):
      return
    if action is None:
      print("Agent has no solution and stops in {}".format(agent.state))
      agent.alive = False
      return

    agent.state = action #the action is a move to the neighbouring city
    agent.location = agent.state
    agent.performance -= 1
    print("Agent in {} with performance = {}".format(agent.state, agent.performance))

    if not agent.seq: #the whole solution is executed
      agent.alive = False
      if isinstance(agent.goal, list):
        print("Agent reached all goals")
      else:
        print("Agent reached the goal: {}".format(agent.goal))
    else:
      self.update_agent_alive(agent)

  def step(self):
    if self.is_done():
      print("There is no one here who could work...")
      return []
    actions = []
    for agent in self.agents:
      if agent.alive:
        action = agent.seq.pop(0) if agent.seq else None
        print("Agent decided to do {}.".format(action))
        self.execute_action(agent, action)
        actions.append(action)
    return actions

  def run(self, steps=10):
    for step in range(steps):
      if self.is_done():
        return
      print("step {0}:".format(step+1))
      self.step()
