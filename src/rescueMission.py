# Lab 4 tasks: one rescue mission = a laboratory + its state-space graph + the environment + the two robots
import io
from contextlib import redirect_stdout, nullcontext

from src.labMazeData import makeLabMaze, defineLabAvailableActions, makeLabTransitionModel, findCell, START, TARGET
from src.labGraphClass import LabGraph
from src.labEnvironmentClass import LabEnvironment
from src.agents import RescueRobotAgentUCS, RescueRobotAgentIDS


def makeLaboratory(seed=None, n=7, solvable=True):
  '''A random laboratory, its state-space graph and the environment with the security drones.
  The same seed gives the same laboratory and the same drones.'''
  lab = makeLabMaze(n, seed=seed, solvable=solvable)
  cellTM = makeLabTransitionModel(defineLabAvailableActions(lab))
  graph = LabGraph(cellTM, findCell(lab, START), findCell(lab, TARGET))
  env = LabEnvironment(lab, cellTM, len(graph.nodes()), seed=seed)
  return lab, graph, env


def runRescueMission(seed=None, n=7, solvable=True, quiet=True):
  '''Both robots (UCS and IDDFS) start from the same cell of the same laboratory and try to reach the same target.
  quiet=True keeps the step-by-step log in env.log instead of printing it.
  Returns the environment (env.agents = [UCS Robot, IDDFS Robot]).'''
  lab, graph, env = makeLaboratory(seed, n, solvable)
  log = io.StringIO()
  with redirect_stdout(log) if quiet else nullcontext():
    for robot in (RescueRobotAgentUCS(graph.start, graph, graph.target), RescueRobotAgentIDS(graph.start, graph, graph.target)):
      env.add_thing(robot)
    env.run()
  env.log = log.getvalue()
  return env
