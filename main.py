import pandas as pd
import os
from Routes import*
from pulp import *
from formulation import *
from simulation import *
from math import isclose
from visuals import*
import openrouteservice as ors
import folium
'''
HOW TO RUN MAIN:
Set desired code chuck to true to run

If running comparsion between both distribution centres open and Southern distribution centre open 
carefully follow these instructions:

WEEKDAY Comparision
-Set Solve Monday-Friday (both centres) to true
-Set Solve for Monday-Friday (South centre only) to true
-Set Comparision for weekdays to true

WEEKEND Comparisions
-Set Solve for Saturday (both centres) to true
-Set Solve for Saturday (South Centre only) to true
-Set Comparisions for weekends to true
'''

# Get location sets
North, South = BothCentresOpen('Data' + os.sep+ 'WarehouseDistances.csv')

# Get pallet demand
North_Mon_to_Fri, North_Sat = DemandData(filename = 'Data' + os.sep +  'demandDataUpdated2.csv', Dataset = North)
South_Mon_to_Fri, South_Sat = DemandData(filename = 'Data' + os.sep +  'demandDataUpdated2.csv', Dataset = South)
nSimulations=10000
'''
Both Centre Trucking schedules
'''
# Solve for Monday-Friday (both centres)
if False:
	# Get series of all stores
	stores = pd.concat([North,South])

	# Get travel times
	northTravelTimes = getTravelTimes(North.append(pd.Series(['Distribution North'], index = ['Distribution North'])), 'Data' + os.sep + 'WarehouseDurations.csv')
	southTravelTimes = getTravelTimes(South.append(pd.Series(['Distribution South'], index = ['Distribution South'])), 'Data' + os.sep + 'WarehouseDurations.csv')
	# Merged travelTimes
	travelTimesAll = pd.concat([northTravelTimes,southTravelTimes], sort = True)
	travelTimesAll.fillna(0,inplace  = True)

	# Get feasible Routes
	northRoutesDF, northRouteCost, northRouteStores = FindStoreSets('Distribution North', North_Mon_to_Fri,northTravelTimes, "northRoute")
	southRoutesDF, southRouteCost, southRouteStores = FindStoreSets('Distribution South', South_Mon_to_Fri,southTravelTimes,"southRoute")

	# Merge routeStores
	routeStores = pd.concat([northRouteStores,southRouteStores])

	# Merge feasible routes together
	routeDataFrame = pd.concat([northRoutesDF,southRoutesDF], sort = True)
	routeDataFrame.fillna(0,inplace  = True)
	routeCost = northRouteCost.append(southRouteCost)

	# Solve LP
	probBothWeek  = solve_LP(routeDataFrame, routeCost, "Mon-FriGrouped")

	# Get optimal Routes
	optimalRouteSeries = getOptimalRouteNamesandStores(probBothWeek,routeDataFrame, routeStores)
	# plot routes
	plotStoreRoutes(optimalRouteSeries,'Data' + os.sep + 'WarehouseLocationsUpdated.csv', 'weekdayBoth')

	# Run Simulation
	cost1 = runSimulation(optimalRouteSeries,nSimulations,stores,True,travelTimesAll,0,'weekdayBoth')

#Solve for Saturday (both centres)
if False:
	# Remove stores with no demand on Saturday
	for store in North_Sat.index:
		if (North_Sat['Pallet Demand'][store] == 0):
			North_Sat = North_Sat.drop(labels = store)
			North = North.drop(labels = store)

	for store in South_Sat.index:
		if (South_Sat['Pallet Demand'][store] == 0):
			South_Sat = South_Sat.drop(labels = store)
			South = South.drop(labels = store)

	stores1 = pd.concat([North,South])

	# Get travel times
	northTravelTimesSat = getTravelTimes(North.append(pd.Series(['Distribution North'], index = ['Distribution North'])), 'Data' + os.sep + 'WarehouseDurations.csv')
	southTravelTimesSat = getTravelTimes(South.append(pd.Series(['Distribution South'], index = ['Distribution South'])), 'Data' + os.sep + 'WarehouseDurations.csv')
	# Merged travelTimes
	travelTimesAll1 = pd.concat([northTravelTimesSat,southTravelTimesSat], sort = True)
	travelTimesAll1.fillna(0,inplace  = True)

	# Get feasible routes
	northRoutesDFSat, northRouteCostSat, northRoutesStoresSat = FindStoreSets('Distribution North', North_Sat,northTravelTimesSat, "northRoute")
	southRoutesDFSat, southRouteCostSat, southRoutesStoresSat = FindStoreSets('Distribution South', South_Sat,southTravelTimesSat,"southRoute")

	# Merge feasible routes
	routeDataFrameSat = pd.concat([northRoutesDFSat,southRoutesDFSat], sort = True)
	routeDataFrameSat.fillna(0,inplace  = True)
	routeCostSat = northRouteCostSat.append(southRouteCostSat)

	# More routeStoreSets
	routeStoreSets = pd.concat([northRoutesStoresSat,southRoutesStoresSat])

	# Solve LP
	probBothSat = solve_LP(routeDataFrameSat, routeCostSat, "SatPrecise")

	# Get optimal Routes
	optimalRouteSeries2 = getOptimalRouteNamesandStores(probBothSat,routeDataFrameSat, routeStoreSets)

	# plot routes
	plotStoreRoutes(optimalRouteSeries2,'Data' + os.sep + 'WarehouseLocationsUpdated.csv', 'weekendBoth')

	# Run Simulation
	cost2 = runSimulation(optimalRouteSeries2,nSimulations,stores1,False,travelTimesAll1,1, 'weekendBoth')

'''
Southern Centre only Trucking schedules
'''
# Solve for Monday-Friday (South Centre Only)
if False:
	# Get travel times
	Mon_Fri_All = pd.concat([North_Mon_to_Fri,South_Mon_to_Fri,])
	stores3 = pd.concat([North, South])
	travelTimes_All3 = getTravelTimes(stores3.append(pd.Series(['Distribution South'], index = ['Distribution South'])),'Data' + os.sep + 'WarehouseDurations.csv')

	# Get feasible Routes
	RoutesDataFrameSouth, routeCostSouth, routeStoresSouth = FindStoreSets('Distribution South', Mon_Fri_All,travelTimes_All3, "Route")

	# Solve LP
	probSouthWeek = solve_LP(RoutesDataFrameSouth, routeCostSouth, "Mon-FriGrouped")

	# routeWeekdaySouth = getOptimalRoutes(probSouthWeek,RoutesDataFrameSouth)
	optimalRouteSeries3 = getOptimalRouteNamesandStores(probSouthWeek,RoutesDataFrameSouth, routeStoresSouth)

	# plot routes
	plotStoreRoutes(optimalRouteSeries3,'Data' + os.sep + 'WarehouseLocationsUpdated.csv', 'weekdaySouth')

	# Run Simulation
	cost3 = runSimulation(optimalRouteSeries3,nSimulations,stores3,True,travelTimes_All3,2, 'WeekdaySouth')

# Solve for Saturday (South Centre Only)
if False:
	# Filter for stores with demand
	Sat_All = pd.concat([North_Sat,South_Sat])
	stores4 = pd.concat([North,South])
	for store in Sat_All.index:
		if (Sat_All['Pallet Demand'][store] == 0):
			Sat_All = Sat_All.drop(labels = store)
			stores4 = stores4.drop(labels = store)

	# Get travel times
	travelTimes_AllSat = getTravelTimes(stores4.append(pd.Series(['Distribution South'], index = ['Distribution South'])),'Data' + os.sep + 'WarehouseDurations.csv')

	# Get Feasible Routes
	routesDataFrameSat, routeCostSat, routeStoresSouthSat  = FindStoreSets('Distribution South', Sat_All, travelTimes_AllSat, "Route")

	# Solve LP
	probSouthSat = solve_LP(routesDataFrameSat,routeCostSat, "SatPrecise")

	# Get optimal Routes
	optimalRouteSeries4 = getOptimalRouteNamesandStores(probSouthSat,routesDataFrameSat, routeStoresSouthSat)

	# plot routes
	plotStoreRoutes(optimalRouteSeries4,'Data' + os.sep + 'WarehouseLocationsUpdated.csv', 'weekendSouth')

	# Run Simulation
	cost4 = runSimulation(optimalRouteSeries4,nSimulations,Sat_All,False,travelTimes_AllSat,3, 'WeekendSouth')


'''
Comparisions
'''
# Comparsions for weekdays
if False:
	'''
	To run make sure both weekday simulations are True above
	'''
	# run two sample t-test
	twoSample_t_test(cost3,cost1)

# Comparions for weekends
if False:
	'''
	To run make sure both weekend simulations are True above
	'''
	# run two sample t-test
	twoSample_t_test(cost4,cost2)
