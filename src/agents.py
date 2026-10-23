# from src.agentPrograms import *
# from src.agentClass import Agent

# from src.rules import vacuumRules
# from src.rules import actionList
# from src.rules import table




# '''Randomly choose one of the actions from the vacuum environment'''
# def RandomVacuumAgent():
#     return Agent(RandomAgentProgram(actionList))


# def TableDrivenVacuumAgent():
#      return Agent(TableDrivenAgentProgram(table))
 
 
# def ReflexAgent() :
#   return Agent(ReflexAgentProgram(vacuumRules,interpret_input,rule_match))


# def ReflexAgentA2pro():
#     pass
#     #your code here
  

# for the Assignment3

import math

from src.PS_agentPrograms import A_StarSearchAgentProgram
from src.mazeProblemSolvingAgentSMARTClass import MazeProblemSolvingAgentSMART
#from vacuumProblemSolvingAgentShowClass import VacuumProblemSolvingAgentDraw
#from src.navProblemSolvingAgentClass import navProblemSolvingAgent

def ProblemSolvingMazeAgentAstar(initState,mazeWorldGraph,goalState):
    #Astar_AP_EvcDist=A_StarSearchAgentProgram(math.dist)
    #return MazeProblemSolvingAgentSMART(initState,mazeWorldGraph,goalState,Astar_AP_EvcDist)
    return MazeProblemSolvingAgentSMART(initState,mazeWorldGraph,goalState,A_StarSearchAgentProgram(math.dist))


# def ProblemSolvingMazeAgentBFS(initState,mazeWorldGraph,goalState):
#     return MazeProblemSolvingAgentSMART(initState,mazeWorldGraph,goalState,BestFirstSearchAgentProgram())

 
# def ProblemSolvingNavAgentBFS(initState,WorldGraph,goalState):
#     return navProblemSolvingAgent(initState,WorldGraph,goalState,BestFirstSearchAgentProgram())

# def ProblemSolvingVacuumAgentBFSwithShow(initState,vacuumWorldGraph,goalState):
#     return VacuumProblemSolvingAgentDraw(initState,vacuumWorldGraph,goalState,BestFirstSearchAgentProgramForShow())

# for the Assignment 5 (PacMan World)

from src.PS_agentPrograms import IDA_StarSearchAgentProgram, RBFSAgentProgram
from src.pacmanAgentClass import PacmanAgent
from src.heuristics import mazeCostHeuristic


def PacmanAgentAstar(initState, mazeWorldGraph, foods, exitState, space_cells,
                     h=mazeCostHeuristic, rational=True, name='Pac-Man (A*)', verbose=True):
    return PacmanAgent(initState, mazeWorldGraph, foods, exitState,
                       A_StarSearchAgentProgram(h, verbose=False, report=False),
                       space_cells, rational, name, verbose)


def PacmanAgentIDAstar(initState, mazeWorldGraph, foods, exitState, space_cells,
                       h=mazeCostHeuristic, rational=True, name='Pac-Man (IDA*)', verbose=True,
                       max_expansions=None):
    return PacmanAgent(initState, mazeWorldGraph, foods, exitState,
                       IDA_StarSearchAgentProgram(h, verbose=False, report=False, max_expansions=max_expansions),
                       space_cells, rational, name, verbose)


def PacmanAgentRBFS(initState, mazeWorldGraph, foods, exitState, space_cells,
                    h=mazeCostHeuristic, rational=True, name='Pac-Man (RBFS)', verbose=True,
                    max_expansions=None):
    return PacmanAgent(initState, mazeWorldGraph, foods, exitState,
                       RBFSAgentProgram(h, verbose=False, report=False, max_expansions=max_expansions),
                       space_cells, rational, name, verbose)
