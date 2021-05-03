import pandas as pd
from pulp import *

def solve_LP(routes, costs, problem):
    '''Solves the linear program

    Parameters
    ----------
    routes: pd.Dataframe
        A dataframe containing the possible routes, each column is one route
    costs: pd.Series
        A list of the costs associated with each route in the routes dataframe
    problem: str
        Name of the file to write the problem to

    Returns
    -------
    prob: puLP problem object
        The problem object
    '''
    # create variables
    route_vars=LpVariable.dicts("Choose",costs.index,cat='Binary')

    # create problem
    prob = LpProblem(problem, LpMinimize)

    # objective function 
    prob += lpSum([route_vars[i]*costs[i]  for i in costs.index]) #need to modify to take care of extra trucks 

    # contraints 
    # each node only gone through once
    for node in routes.index:
        prob += lpSum([route_vars[i]*routes.loc[node][i] for i in costs.index]) == 1

    # 25 trucks available, 2 shifts
    prob += lpSum([route_vars[i] for i in costs.index if 'b' not in i]) <= 50

    # write problem 
    prob.writeLP(problem)

    #Solve LP
    prob.solve()

    #Print objective function value
    print("Minimum cost = ", value(prob.objective))

    # # testing (prints) total number of routes and if each store is visited
    # # Print optimal variable values
    # #counter = routes['northRoute0']*0
    # routesCounter = 0
    # for v in prob.variables():
    #    if v.varValue != 0:
    #        #print(v.name, "=", v.varValue)
    #        #counter += routes[v.name[7:]]
    #        routesCounter += 1
    # #print(counter)
    # print(routesCounter)

    print(LpStatus[prob.status])

    return prob