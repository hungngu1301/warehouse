import numpy as np
import pandas as pd
import random
from math import isclose

def BothCentresOpen(filename):
    ''' Creates 2 arrays that seperate locations
    
    Parameters
    ----------
    filename : string
        Excel file that contains distances from distribution centres

    Returns 
    -------
    North : np.array
        Array of strings that contain locations closer to the North distribution centre
    South : np.array
        Array of strings that contain locations closer to the South distribution centre
    
    Notes
    -----
    Make sure Excel file has South distribution centre in first column and first row and
    North distribution centre in second column and second row
    '''

    # Import data and make array
    Names = np.genfromtxt(filename, dtype = str, delimiter = ',', usecols = 0, skip_header = 1)
    Distances = np.genfromtxt(filename, dtype = float, delimiter = ',', usecols = (1,2), skip_header = 1)

    North = []
    South = []
    i = 0

    # Making node sets
    while i < len(Distances):
        if Distances[i,0] < Distances[i,1] and Distances[i,0] != 0:
            South = np.append(South,Names[i])
        elif Distances[i,0] > Distances[i,1] and Distances[i,1] != 0:
            North = np.append(North,Names[i])
        i += 1

    North = pd.Series(North, index = North)
    South = pd.Series(South, index = South)
    return North, South

def DemandData(filename, Dataset):
    ''' Creates Data frame of the demand data for each location on each day seperation
    
    Parameters
    ----------
    filename: String
        Excel file that stores the demand data
    Dataset : pandas.series
        Dataset that has the names of the locations in the route
    
    Returns
    -------
    Dataset_Mon_to_Fri : pandas.dataset
        Dataset that has the pallet demands of the North locations on Mon to Fri
    Dataset_Sat : pandas.dataset
        Dataset that has the pallet demands of the North locations on Sat
    '''
    # Get pallet demand
    Demand = pd.read_csv(filename)

    # Obtain list of pallet demand values for Mon to Fri and Saturday
    Mon_to_Fri_Data = Demand.iloc[:]['Mon-Fri'].tolist() 
    Sat_Data = Demand.iloc[:]['Sat'].tolist() 

    # Create Pandas series of demand data
    Mon_to_Fri = pd.Series(Mon_to_Fri_Data, index = Demand.iloc[:]['Name'])
    Sat = pd.Series(Sat_Data, index = Demand.iloc[:]['Name'])

    # Make Dataframe that contains locations and pallet demands
    Dataset_Mon_to_Fri = pd.DataFrame({'Name' : Dataset, 'Pallet Demand' : Mon_to_Fri})
    Dataset_Mon_to_Fri = Dataset_Mon_to_Fri.dropna() # Delete NaN rows
    del Dataset_Mon_to_Fri['Name'] # Remove "Name" column

    Dataset_Sat = pd.DataFrame({'Name' : Dataset, 'Pallet Demand' : Sat})
    Dataset_Sat = Dataset_Sat.dropna()# Delete NaN rows
    del Dataset_Sat['Name'] # Remove "Name" column

    return Dataset_Mon_to_Fri, Dataset_Sat

def getTravelTimes(stores,filepath):
    '''Gets travel times between stores

        Parameters
        ---------
        stores: pd.Series
            A series of stores (includes distribution centers)
        filepath: str
            Name of the file that contains the travel times

        Returns
        -------
        travelTimes: pd.Dataframe
            A dataframe containing the travel times between the stores
    
        Notes
        ----
        The file specified in filepath should be a CSV that contains a matrix of travel times between all
        the different Warehouse Group stores and their distribution centres

    '''
    # Get travel times
    travelTimes = pd.read_csv(filepath, index_col=0)

    # Make Dataframe of locations and travel times
    for columns in travelTimes.columns: # Deleting columns not in stores set
        if columns not in stores:
            travelTimes = travelTimes.drop(labels = columns, axis = 1)
            

    for row in travelTimes.index: #Deleting rows not in stores set
        if row not in stores:
            travelTimes = travelTimes.drop(labels = row)
            
    return travelTimes

def RouteLength(stores, storeTravelTimes,pallets, nextStore = None):
    '''Calculates the total route length between the stores 

        Parameters
        ----------
        stores: list
            A list of the stores to be visited (includes distribution centres)
        storeTravelTimes: pd.dataframe
            Dataframe containing the travel times between all the stores and distribution centres
        pallets: int
            The number of pallets
        nextStore: str (optional)
            Next store to add to list
        
        Returns
        -------
        travelTime: double
            The total time to visits all the stores
    '''
    travelTime = 0
    if (nextStore != None):
        stores.insert(-1, nextStore)
    
    for store1,store2 in zip(stores[0:],stores[1:]):
        travelTime += storeTravelTimes.at[store1,store2]

    travelTime  += pallets*600

    if (nextStore != None):
        del stores[-2]
  
    return travelTime

def FindStoreSets(distributionCenter, storeDemandEstimates, storeTravelTimes, routeName):
    '''Finds sets of routes that can be linked to form feasible route
    
    Parameters
    ----------
    distributionCenter: str
        Name of the distribution center the routes start and end at
    storeDemandEstimates: pd.dataframe
        Dataframe containing store name as index and column of daily pallet demands
    storeTravelTimes: pd.dataframe
        Dataframe containing travel times between the all The Warehouse and Noel Leeming 
        stores.
    routeName: str
        The name assigned to the generated routes

    Returns
    -------
    routesDataFrame: pd.Dataframe
        Dataframe containing the generated feasible routes where each column represents
        a different route and each row corresponds to if the route visits a specific store.
    routesCost: pd.Series
        A series of the costs for each route in the routesDataFrame
    routesStores: pd.Series
        A series that contains an ordered list of stores that each route visits
    '''
    random.seed(80)
    # generate n number of route sets
    n = 1000
    for i in range(n):

        # select first store
        currentStore = storeDemandEstimates.index[random.randint(0, storeDemandEstimates.size-1)]
        currentStoreSet = [distributionCenter,currentStore,distributionCenter]

        totalPallets = storeDemandEstimates.at[currentStore,'Pallet Demand']
        numStore = random.randint(2,5) # maximum number of stores in route

        # feasible route conditions: cannot take longer than 4 hours, cannot have more than numStore stores
        keep_looping = True
        while  ((len(currentStoreSet)-2 < numStore) & (RouteLength(currentStoreSet,storeTravelTimes, totalPallets) <= 14400) & keep_looping):

            # select next store 
            sortedTravelTimes = storeTravelTimes.drop([currentStore, distributionCenter]).sort_values(by = [currentStore])
            nextStore = sortedTravelTimes.index[random.randint(0, 2)]
            
            # check adding store is valid
            if ((not (nextStore in currentStoreSet)) & (RouteLength(currentStoreSet,storeTravelTimes,totalPallets, nextStore)<= 14400)):
                if (totalPallets + storeDemandEstimates.at[nextStore, 'Pallet Demand'] <= 20):
                    currentStoreSet.insert(-1,nextStore)
                    totalPallets += storeDemandEstimates.at[nextStore, 'Pallet Demand']
                    currentStore = nextStore
                else:
                    keep_looping = False
            else:
                keep_looping = False
            

        # Find stores that route vists
        route = pd.Series([1 if store in currentStoreSet else 0 for store in storeDemandEstimates.index],index = storeDemandEstimates.index)
        
        # if first route create dataframe otherwise just add to dataframe
        if (i==0): 
            cost = [(RouteLength(currentStoreSet,storeTravelTimes, totalPallets)/3600)*175, 1500]
            routes = [routeName + str(i), routeName + str(i) + "b" ]
            stores = [currentStoreSet, currentStoreSet]
            routeDataFrame = pd.DataFrame({routeName + "0":route})
            routeDataFrame[routeName+ str(i)+ 'b'] = route

        else:
            routeDataFrame[routeName + str(i)] = route
            routeDataFrame[routeName + str(i) + 'b'] = route

            routes.extend([routeName + str(i), routeName + str(i) + 'b'])
            stores.extend([currentStoreSet, currentStoreSet])
            cost.extend([(RouteLength(currentStoreSet,storeTravelTimes,totalPallets)/3600)*175, 1500])

    routesCost = pd.Series(cost,index = routes)
    routeStores = pd.Series(stores,index=routes)

    return routeDataFrame, routesCost, routeStores

def getOptimalRoutes(problem, routesDF):
    '''Get the stores for each selected route

    Parameters
    ---------
    problem: puLP problem object 
        The problem object that is optimally solved
    routesDF: pd.Dataframe
        A dataframe containing the routes fed into the LP

    Returns
    -------
    opitmalRoutes: list
        A list of routes where each element of the list is a list of stores visited
        in an optimal route
    '''

    optimalRoutes = []
    route = []

    for v in problem.variables():
        
        # check if route is selected
        if (isclose(v.varValue,1)):
            stores = routesDF.iloc[:,0]*0 + routesDF[v.name[7:]]
            print(stores)
            
            # Add names of selected stores into route
            route.clear()
            route = [store if stores.loc[store] !=0 else 0 for store in stores.index]
            route = [i for i in route if i != 0]
            

            optimalRoutes.append(route.copy())
    
    return optimalRoutes


def getOptimalRouteNamesandStores(problem, routesDF, storeRoutes):
    '''Get the stores for each selected route

    Parameters
    ---------
    problem: puLP problem object 
        The problem object that is optimally solved
    routesDF: pd.Dataframe
        A dataframe containing the routes fed into the LP

    Returns
    -------
    opitmalRouteNames: pd.Series
        The optimal routes and the visited stores
    '''

    optimalRouteNames = []
    optimalRoutes = []
    # route = []

    for v in problem.variables():
        if (isclose(v.varValue, 1)):
            # name of optimal route
            optimalRouteNames.append(v.name)
            optimalRoutes.append(storeRoutes[v.name[7:]])
            
            # stores visited
            # stores = routesDF.iloc[:,0]*0 + routesDF[v.name[7:]]
            # route.clear()
            # route = [store if stores.loc[store] !=0 else 0 for store in stores.index]
            # route = [i for i in route if i != 0]
            # optimalRoutes.append(route.copy())

    optimalRoutesSeries = pd.Series(optimalRoutes, index= optimalRouteNames)

    return optimalRoutesSeries
