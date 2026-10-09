# Treasure Maze (Assignment 3 task)
# The state space follows the "Maze State-Space Graph" from the task:
# a node for the start (S), the finish (F), every dead end and every junction / turning point.
# The task picture repeats 4 labels, so the second occurrence (reading top-to-bottom, left-to-right) got "2":
#   E2 - the junction under C,  F2 - the dead end right of E,  J2 - the junction under E2,  L2 - the junction under H
# Every edge is one corridor of the maze, its cost = 1 (one move)

mazeData = dict(
    S=dict(M=1, N=1),
    A=dict(B=1, E=1),
    B=dict(C=1, G=1),
    C=dict(D=1, E2=1),
    D=dict(F=1, H=1),
    E=dict(I=1, F2=1),
    G=dict(J=1, E2=1),
    E2=dict(J2=1),
    H=dict(L2=1),
    I=dict(M=1, J=1),
    J=dict(Q=1, J2=1),
    J2=dict(R=1, L=1),
    L=dict(L2=1),
    L2=dict(K=1),
    Q=dict(N=1, R=1),
    R=dict(O=1),
    K=dict(P=1),
    N=dict(O=1),
    O=dict(P=1)
    )

# (column, row) of every node in the maze picture: x grows to the East, y grows to the South.
# It is used to know the direction (N/E/S/W) of every corridor and to draw the maze.
mazeLocations = dict(
    A=(0, 0), B=(2, 0), C=(4, 0), D=(6, 0), F=(7, 0),
    E=(0, 1), F2=(1, 1), G=(2, 1), E2=(4, 1), H=(6, 1),
    I=(0, 2), J=(2, 2), J2=(4, 2), L=(5, 2), L2=(6, 2),
    M=(0, 3), Q=(2, 3), R=(4, 3), K=(6, 3),
    S=(0, 4), N=(2, 4), O=(4, 4), P=(6, 4))

mazeStart = 'S'
mazeFinish = 'F'
startHeading = 'E' # the Agent enters the maze from the left side, so it is looking to the East

# four types of treasures: name -> (icon, description)
treasureTypes = dict(
    Gold=('🪙', 'Pile of Gold'),
    Diamond=('🔷', 'Diamond'),
    Pizza=('🍕', 'Flyer for 100 Free Pizzas'),
    ExtraPoints=('🎉', '20 Extra Points for the CS3220 Final Exam'))

exitIcon = '🏠'
