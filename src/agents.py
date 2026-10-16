# for the Assignment3

from src.PS_agentPrograms import *
from src.mazeProblemSolvingAgentSMARTClass import MazeProblemSolvingAgentSMART



from src.vacuumProblemSolvingAgentSMARTClass import VacuumProblemSolvingAgentSMART
#from vacuumProblemSolvingAgentShowClass import VacuumProblemSolvingAgentDraw
from src.navProblemSolvingAgentClass import navProblemSolvingAgent
from src.rescueRobotAgentClass import RescueRobotAgent


def ProblemSolvingMazeAgentBFS(initState,mazeWorldGraph,goalState):
    return MazeProblemSolvingAgentSMART(initState,mazeWorldGraph,goalState,BestFirstSearchAgentProgram())


def ProblemSolvingVacuumAgentBFS(initState,vacuumWorldGraph,goalState):
    return VacuumProblemSolvingAgentSMART(initState,vacuumWorldGraph,goalState,BestFirstSearchAgentProgram())

 
def ProblemSolvingNavAgentBFS(initState,WorldGraph,goalState):
    return navProblemSolvingAgent(initState,WorldGraph,goalState,BestFirstSearchAgentProgram())

# Lab 4 tasks: two Rescue Robots in the Hazardous Laboratory Maze
def RescueRobotAgentUCS(initState,labGraph,goalState):
    return RescueRobotAgent(initState,labGraph,goalState,UniformCostSearchAgentProgram(),'UCS Robot')


def RescueRobotAgentIDS(initState,labGraph,goalState):
    return RescueRobotAgent(initState,labGraph,goalState,IDSearchAgentProgram(),'IDDFS Robot')

# def ProblemSolvingVacuumAgentBFSwithShow(initState,vacuumWorldGraph,goalState):
#     return VacuumProblemSolvingAgentDraw(initState,vacuumWorldGraph,goalState,BestFirstSearchAgentProgramForShow())