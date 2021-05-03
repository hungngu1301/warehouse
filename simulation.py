# Functions used to assist in the simulation of our proposed trucking solution
import os
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns
import statistics
import statsmodels.stats.weightstats as sms

def getSimulatedDemands(stores, filepath, n, week):
	'''Creates demand estimates from bootstrap sampling

	Parameters
	----------
	stores: pd.Series
		A series of all the stores to create demand estimates for
	filepath: str
		The filepath of the csv file that contains the demand data for The Warehouse Group Stores
	n: int
		The number of simulated demands to generate for each store
	weekday: bool
		If weekend or weekday demand simulations are wanted

	Returns
	--------
	simulatedDemands: pd.Dataframe
		A dataframe containing the demand estimates, where each row is the demand estimates for a store

	Notes
	----
	'''
	# read in demand data
	demandData = np.genfromtxt(filepath, skip_header=1,delimiter=',')[:,1:]
	
	# extract relevant demand data 
	if (week):
		weekday = np.array([0,1,2,3,4,7,8,9,10,11,14,15,16,17,18,21,22,23,24,25])
		noelLeemingDemand = demandData[0:20,weekday].flatten()
		warehouseDemand = demandData[20:,weekday].flatten()
	else:
		weekend = np.array([5,6,12,13,19,20,26,27])
		noelLeemingDemand = demandData[0:20,weekend].flatten()
		warehouseDemand = demandData[20:,weekend].flatten()

	simulatedDemands = []
	# simulate demand for each store
	for store in stores.index:
		if (store == 'Noel Leeming Grouped Stores'):
			simulatedDemand = [noelLeemingDemand[i] for i in np.random.randint(0,len(noelLeemingDemand),size = n)] 
			simulatedDemand2 = [noelLeemingDemand[i] for i in np.random.randint(0,len(noelLeemingDemand),size = n)]
			simulatedDemands.extend(np.copy([sum(i) for i in zip(simulatedDemand,simulatedDemand2)]))
		elif (store[0:4] == 'Noel'):
			simulatedDemand = [noelLeemingDemand[i] for i in np.random.randint(0,len(noelLeemingDemand),size = n)] 
			simulatedDemands.extend(np.copy(simulatedDemand))

		elif (store[0:3] == 'The'):
			simulatedDemand = [warehouseDemand[i] for i in np.random.randint(0,len(warehouseDemand),size = n)]
			simulatedDemands.extend(np.copy(simulatedDemand))
		else:
			simulatedDemand = [warehouseDemand[i] for i in np.random.randint(0,len(warehouseDemand),size = n)] 
			simulatedDemand2 = [noelLeemingDemand[i] for i in np.random.randint(0,len(noelLeemingDemand),size = n)] 
			simulatedDemands.extend(np.copy([sum(i) for i in zip(simulatedDemand,simulatedDemand2)]))

	# store simulated demands in pandas DataFrame
	simulatedDemands = np.reshape(simulatedDemands, (stores.size, -1))  
	demandsDF = pd.DataFrame(simulatedDemands, index = stores.index)

	return demandsDF

def getSimulatedTime(n,weekday):
	'''
	Returns the random extra time per hour of trip 

	------------ 
	Parameters:
	n: int
		number of simulations
	weekday : boolean 
		If the simulation is done for weekday then True, otherwise, False
	
	------------ 
	Returns:
	extraTime: np.array
		extra minutes per hour of trip for each simulation

	------------ 
	Notes: 
	1) Output is extra minutes per hour
	2) The range is estimated from data on https://www.tomtom.com/en_gb/traffic-index/auckland-traffic/
			
	'''

	if weekday:
		extraTime=np.random.randint(20,60,size = n) #40 mins on avarage 
	else:
		extraTime=np.random.randint(20,40,size = n) #looking at the table on the website, the range can be estimated to be abour 20-40 mins per hour

	return extraTime

def calculateDemand(routes, orignalDemands):
	'''Calculates the demand for each of the selected routes

	Parameters
	----------
	routes: pd.Series
		A series of routes and the stores visited by each route
	orignalDemands: pd.Series
		A series that contains the demand for each store

	Returns
	------
	demandSeries: pd.Series
		A series that contains the orignal demands for each route
	'''
	
	demands = []

	for stores in routes.values:
		demand = 0
		for store in stores[1:-1]:
			demand += orignalDemands['Pallet Demand'][store]
		demands.append(demand)

	demandSeries = pd.Series(demands, index = routes.index)

	return demandSeries

def simulateDemand(routes, simulatedDemands):
	'''Calculates simulated demand for each route
	
	Parameters
	-----------
	routes: pd.Series
		A series of the routes and the stores each route vistes
	simulatedDemands: pd.Dataframe
		A dataframe containing the simulated demands for each store
	
	Returns
	--------
	simulatedDemands: pd.Dataframe
		A dataframe containing the simulated demands for each route
	'''

	for i in range(simulatedDemands.shape[1]):
		demands = []
		for stores in routes.values:
			demand = 0
			for store in stores[1:-1]:
				demand += simulatedDemands[i][store]
			demands.append(demand)
				
		if i == 0:
			simulateRouteDemand = pd.DataFrame({i:demands}, index = routes.index)
		else:
			simulateRouteDemand[i] = demands

	return simulateRouteDemand

def adjustRoutes(storeDemands,routeStores, simulatedRouteDemands,simulatedDemand):
	'''Modifies routes so that no route has more than 20 pallets

	Parameters
	----------
	storeDemands: pd.DataFrame
		A dataframe that contains the simulated demand for each store
	routeStores: pd.Series
		A series that contains the stores visited by each route
	SimlulatedRouteDemands: pd.DataFrame
		A dataframe that contains the simulated demand for each route
	simulatedDemand: pd.DataFrame
		A dataframe that contains the simulated demand for each store
	
	Returns
	--------
	adjustedRouteStores: pd.DataFrame
		A dataframe that contains the stores visitied by each route
	adjustedRouteDeamnds: pd.DataFrame
		A dataframe that contains the new total demand for each adjusted route
	leftOutStores: pd.Series
		A series where each element contains a dictionary of the left out stores and their demand
	'''
	# dictionaries of the removed stores and their demands
	removedDictionaries = []
	numAdjustedRoutes = []

	# for every simulation
	for i in range(simulatedRouteDemands.shape[1]):

		adjustRoutesCounter = 0 # reset counter
		newDemands = []
		newStores = []
		removedStores = []
	
		# for every route
		for route in simulatedRouteDemands.index:
			
			# remove stores from route if pallet demand is greater than 20
			if simulatedRouteDemands[i][route] > 20:
				adjustRoutesCounter += 1

				storeList  = routeStores[route].copy()
				keep_looping = True
				newDemand = simulatedRouteDemands[i][route]

				while (keep_looping):
					removedStores.append((storeList[0],storeList.pop(-2)))
					newDemand -= simulatedDemand[i][removedStores[-1][-1]]
					if (newDemand<=20):
						keep_looping = False				

			else:
				storeList = routeStores[route]
				newDemand = simulatedRouteDemands[i][route]
				
			newDemands.append(newDemand)
			newStores.append(storeList)
		
		# Add adjustedroutes to array
		numAdjustedRoutes.append(adjustRoutesCounter)
		
		# Create dictionary of all the removed stores for simulation i
		storesRemovedDemand = []
		for store in removedStores:
			storesRemovedDemand.append(simulatedDemand[i][store[-1]])
		removedDictionaries.append(dict(zip(removedStores,storesRemovedDemand)))
	

		# populate adjustedRouteStores and adjustedRouteDemands dataframes
		if i == 0:
			adjustedRouteStores = pd.DataFrame({0:newStores},index = simulatedRouteDemands.index)
			adjustedRouteDemands = pd.DataFrame({0:newDemands}, index = simulatedRouteDemands.index)

		else:
			adjustedRouteStores[i] = newStores
			adjustedRouteDemands[i] = newDemands
		
	
	# Populate leftOutStores
	leftOutStores = pd.Series(removedDictionaries)

	# AdjustedRoutes series
	numAdjustedRoutesSeries = pd.Series(numAdjustedRoutes)
	
	return adjustedRouteStores,adjustedRouteDemands,leftOutStores, numAdjustedRoutesSeries

def calculateTime(adjustedRoutes,leftOutStores,extraTime,travelTime,adjustedRoutesDemands):
	'''
	returns the total time of each route for each simulation

	----------
	Parameters: 
	adjustedRoutes: pd.DataFrame
		adjusted routes with no routes more than 20 pallets
	leftOutStores: pd.Series
		stores that are left out due to total demand over 20
	extraTime: np.array 
		array of extra time in minutes per hour of trip
	travelTime: pd.DataFrame
		travel time between stores 
	adjustedRoutesDemands: pd.DataFrame
		Total demands of adjusted routes with no routes more than 20 pallets
	
	----------
	Returns: 
	adjustedRoutesTime: pd.DataFrame
		time of adjusted routes with no routes more than 20 pallets for each simulation
	leftOutStoresTime: pd.Series
		time of trips to stores that are left out due to total demand over 20 for each simulation
	numTrucks: pd.Series
		number of trucks needed for each simulation
	
	----------
	Notes: 
	1) All the time outputs will be in hours
	2) For left out stores, each store will be assigned to 1 truck
	3) adjustedRoutes and adjustedRoutesTime will be the same structure. Same for leftOutStores and leftOutStoreTime.
	4) The adjustedRoutesTime DataFrame will have the structure of 
			1	2	3	4	5	6	...
	Route1
	Route2
	Route3
	...

	5) The leftOutStoresTime pd.Series will have the structure of 		
	1	dictionary1
	2	dictionary2
	3	dictionary3	
	4	
	...

	6) The dictionary in leftOutStoresTime will have the following structure
	{'Distribution Centre, Store1': time1, 'Distribution Centre, Store2': time2, 'Distribution Centre, Store3': time3, ...}
	with time is the time taken to travel from Distribution Centre to the route and back to Distribution Centre including time to move the pallets 
	'''
	#Make a copy 
	adjustedRoutesTime=adjustedRoutes.copy() #time for adjusted routes 
	leftOutStoresTime=leftOutStores.copy() #time for left out stores 
	numTrucks=leftOutStores.copy() #number of trucks each simulation needed

	for i in range(adjustedRoutes.shape[1]):
		#reset trucks counter
		truck = 0

		#Loop through all routes in adjusted routes 
		for route in adjustedRoutes.index:
			#reset time
			time = 0

			#add 1 truck
			truck += 1

			#Calculate travel time
			for store1,store2 in zip(adjustedRoutes.at[route,i][0:],adjustedRoutes.at[route,i][1:]):
				time += travelTime.at[store1,store2]
			
			#Calculate extra time due to traffic
			time += time/3600*extraTime[i]*60

			#Pallets moving time 
			time += adjustedRoutesDemands.at[route,i]*600

			#Convert time to hours and assign 
			adjustedRoutesTime.at[route,i]=time/3600

		#check if the dictionary is empty
		if len(leftOutStores[i])!=0:
			#loop through all left out stores 
			for store in leftOutStores[i]:
				#add 1 truck
				truck += 1

				#reset time
				time = 0

				#initialise the route
				route = [store[0], store[1],store[0]]

				#calculate and add travel time into time
				for store1,store2 in zip(route[0:],route[1:]):
					time += travelTime.at[store1,store2]
				
				#2 trucks for demand over 20, then double the time
				if leftOutStores[i][store] > 20:
					truck += 1 
					time += time
				
				#extra time due to traffic  
				time += time/3600*extraTime[i]*60

				#pallets moving time, not affected by traffic 
				time += leftOutStores[i][store]*600 

				#Convert time to hours and assign 
				leftOutStoresTime[i][store]=time/3600
		
		#Assign number of trucks 
		numTrucks[i]=truck

	return adjustedRoutesTime,leftOutStoresTime,numTrucks

def calculateCost(adjustedRoutesTime,leftOutStoresTime):
	'''
	returns the total cost of model for each simulation

	----------
	Parameters: 
	adjustedRoutesTime: pd.DataFrame
		time of adjusted routes with no routes more than 20 pallets
	leftOutStoresTime: pd.Series
		time of trips to stores that are left out due to total demand over 20
	
	----------
	Returns: 
	cost: pd.Series
		total cost of the model for each simulation
	
	----------
	Notes: 
	1) adjustedRoutesTime is expected to have structure of  
			1	2	3	4	5	6	...
	Route1
	Route2
	Route3
	time will be in hours
	...
	2) The leftOutStoresTime pd.Series will have the structure of 		
	1	dictionary1
	2	dictionary2
	3	dictionary3	
	4	
	...

	3) The dictionary in leftOutStoresTime will have the following structure
	{'DC, Store1': time1, 'DC, Store2': time2, 'DC, Store3': time3, ...} 
	with DC is the corresponding Distribution Centre of Store and time in hours
	
	4) The Cost pd.Series will have the structure of 		
	1	Total cost for simulation 1
	2	Total cost for simulation 2
	3	Total cost for simulation 3
	4	Total cost for simulation 4
	...	

	'''
	#Make a copy
	costDataFrame=leftOutStoresTime.copy()

	#Loop through all simulations
	for i in adjustedRoutesTime.columns:
		#reset cost
		cost = 0 

		#Loop through all routes
		for j in adjustedRoutesTime.index:
			#if time is over 4 hours
			if adjustedRoutesTime.at[j,i] >= 4:
				#consider extra costs
				cost += (adjustedRoutesTime.at[j,i]-4)*250 + 175*4
			else: 
				#normal cost 175 per hour
				cost += adjustedRoutesTime.at[j,i]*175
		
		#Check if there are no left out stores
		if len(leftOutStoresTime[i]) !=0:
			#Loop through all left out stores 
			for j in leftOutStoresTime[i].keys():
				#assign time
				time=leftOutStoresTime[i][j]

				#check if time is over 4 hours
				if time >= 4:
					cost += (time-4)*250 + 175*4
				else: 
					#normal cost 175 dollars per hour
					cost += time * 175
		#Assign time
		costDataFrame[i]=cost

	return costDataFrame

def plotSimulatedCosts(costDataFrame, colour,name):
	'''Plots the distribution of the simulated costs

	Parameters
	----------
	costDataFrame; pd.Series
		A series that contains the cost for each simulation
	colour: int
		The colour of the plot
	name: string
		Name of the graph
	'''
	colours  = sns.color_palette(palette='muted',n_colors=4)
	
	costDataFrame = costDataFrame.sort_values()
	
	sns.set_style("darkgrid")
	sns.distplot(costDataFrame,hist = True,color = colours[colour])
	plt.xlabel('Cost of Routing Schedule [$]',fontsize=14)
	plt.title('Distribution of Simulated Cost for Routing Schedule',fontsize=18)
	plt.axvline(costDataFrame.iloc[int(costDataFrame.shape[0]*0.025)], color = 'black')
	plt.axvline(costDataFrame.iloc[int(costDataFrame.shape[0]*0.975)], color = 'black')

	print(costDataFrame.iloc[int(costDataFrame.shape[0]*0.025)])
	print(costDataFrame.iloc[int(costDataFrame.shape[0]*0.975)])

	#plt.show()
	plt.savefig('SimulationPlots' + os.sep + name+'Cost')
	plt.clf()

	return None

def plotTrucks(trucks,colour,name):
	'''Plots the bar graph of the number of trucks needed to complete a routing schedule 

	Parameters
	----------
	trucks pd.Series
		A series that contains the cost for each simulation
	colour: int
		The colour of the plot
	name: string
		Name of the graph
	'''
	colours  = sns.color_palette(palette='muted',n_colors=4)
	sns.set_style("darkgrid")
	sns.distplot(trucks, hist = True, color=colours[colour],kde = False)

	plt.xlabel('Number of Trucks',fontsize=14)
	plt.ylabel("Frequency",fontsize=14)
	plt.title('Distribution of the Number of Truck Shifts Required', fontsize=18)
	#plt.show()

	plt.savefig('SimulationPlots' + os.sep + name+'Trucks')
	plt.clf()

	return None

def plotNumAdjustedRoutes(numAdjustedRoutes,colour,name):
	'''Plots the bar graph of the number of trucks needed to complete a routing schedule 

	Parameters
	----------
	numAdjustedRoutes: pd.Series
		A series that contains the number of adjusted routes in each simulation
	colour: int
		The colour of the plot
	name: string
		Name of the graph
	'''
	colours  = sns.color_palette(palette='muted',n_colors=4)
	sns.set_style("darkgrid")
	sns.distplot(numAdjustedRoutes, hist = True, color=colours[colour],kde = False)

	plt.xlabel('Number of Routes Adjusted', fontsize=14)
	plt.ylabel("Frequency",fontsize=14)

	plt.title('Distribution of the Number of Routes Adjusted',fontsize=18)
	#plt.show()

	plt.savefig('SimulationPlots' + os.sep + name+'AdjustedRoutes')
	plt.clf()

	return None

def runSimulation(optimalRoutes,nSimulation, storeSeries, weekday, travelTimes, colour,name):
	'''Runs Simulation for routing schedule

	Parameters
	--------
	optimalRoutes: pd.Series
		A series that contains the selected routes and an order store list
	estimatedStoreDemands: pd.Series
		A series that contains the estimated demand for each store in routing schedule
	nSimulation: int
		The number of simulations to run
	storeSeries: pd.Series
		A series of the stores in the routing schedule
	weekday: bool
		If simulation is for weekend or weekday
	travelTimes: pd.DataFrame
		A dataframe that contains the travel time between all the stores in the routing scheule
	colour: int
		The colour of the generated histogram
	name: str
		The name of the file that the figure is saved to

	'''
	
	# Get simulated demands for each route
	simulatedDemand = getSimulatedDemands(storeSeries,'Data' + os.sep + 'demandDataUpdated.csv', nSimulation, weekday)
	simulatedRouteDemand = simulateDemand(optimalRoutes,simulatedDemand)

	#Adjust routes so each route does not exceed 20 pallets
	adjustedRouteStores,adjustedRouteDemands,leftOutStores,numAdjustedRoutes = adjustRoutes(storeSeries,optimalRoutes,simulatedRouteDemand, simulatedDemand)

	# Calculate Time of each route
	extraTime=getSimulatedTime(nSimulation, weekday)
	adjustedRoutesTime,leftOutStoresTime, numTrucks=calculateTime(adjustedRouteStores,leftOutStores,extraTime,travelTimes,adjustedRouteDemands)
	
	# For Anton: numTrucks will have same structure as cost with total number of trucks used for each simulation instead of total cost
	# you can find the number of EXTRA trucks by just do extraTrucks = numTrucks - len(adjustedRouteStores.index)

	# Calculate Cost of routing schedule
	cost = calculateCost(adjustedRoutesTime,leftOutStoresTime)
	
	# Plot Number of trucks
	plotTrucks(numTrucks,colour,name)

	# Plot distribution of costs
	plotSimulatedCosts(cost, colour,name)

	# Plot Number of routes that exceeded 20 pallets
	plotNumAdjustedRoutes(numAdjustedRoutes, colour,name)

	return cost

def twoSample_t_test(cost1,cost2):
	'''Runs a two sample t-test on the cost arrays

	Parameters
	---------
	cost1: pd.Series
		A series of costs
	cost2: pd.Series
		A series of costs
	'''
	cost1Array =  cost1.to_numpy()
	cost2Array = cost2.to_numpy()

	twoSamp = sms.CompareMeans(sms.DescrStatsW(cost1Array),sms.DescrStatsW(cost2Array))
	print(twoSamp.ttest_ind())
	print(twoSamp.tconfint_diff())	

	return None

