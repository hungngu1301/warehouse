import numpy as np
import pandas as pd
import folium
import os
import openrouteservice as ors


def displayStores():
    '''Plots the store locations on folium map
    '''

    locations = pd.read_csv("Data" + os.sep + "WarehouseLocationsUpdated.csv")
    #print(locations)

    coords = locations[['Long','Lat']]
    coords = coords.to_numpy().tolist()

    m = folium.Map(location = list(reversed(coords[2])), zoom_start=10)
    folium.Marker(list(reversed(coords[0])), popup = locations.Store[0], icon = folium.Icon(color = 'black')).add_to(m)
    for i in range(1, len(coords)):
        if locations.Type[i] == "The Warehouse":
            iconCol = "red"
        elif locations.Type[i] == "Noel Leeming":
            iconCol = "orange"
        elif locations.Type[i] == "Combined":
            iconCol = "green"
        elif locations.Type[i] == "Distribution":
            iconCol = "black"
        folium.Marker(list(reversed(coords[i])), popup = locations.Store[i], icon = folium.Icon(color = iconCol)).add_to(m) 

    m.save('StoreLocations.html')

    return None

def plotStoreRoutes(routes, filename, name):
    '''Plots routes
    Parameters
    ----------
    routes: list
        A list of lists where each element of the list is a list of stores visited by in a route
        
        Notes
        ------
        Saves the generated map as filename
        '''
    m = folium.Map(location = [-36.998761,174.874272], zoom_start=10)
    coords = []
    #reading locations into a data frame
    locations = pd.read_csv(filename, index_col='Store')
    client = ors.Client(key='5b3ce3597851110001cf6248060b6d84cf244f1c9f3cd208e086323b')
    Counter_North = 0 #Initialise counter for North route colors
    Counter_South = 0 #Initialise counter for South route colors
    ColorIndex_North = ['#3BBD9B','#44DBB4','#319C80','#73E5D3','#A1DDE0','#B2E3E6','#537273','#64898B','#79A6A8','#92C9CC',
    '#445F5F','#1C3738','#A5CBC0','#9FD2CD','#00D559']
    ColorIndex_South = ['#E80000','#FF0000','#FF4200','#FF6300','#FF8300','#FFBB00','#FFE300','#DDF300','#BAF700','#98FB00',
    '#75FF00','#4BFF00','#5CFF60','#4FFF8F','#49FFA7','#42FFBE','#3AFFDE','#36FFEE','#31FFFD']

    for Path in routes:
        for store in Path:
            store_coords = [locations.at[store,'Long'],locations.at[store,'Lat']]
            coords.append(store_coords)   

        route = client.directions(
            coordinates = coords,
            profile = 'driving-hgv', # driving-hgv.
            format='geojson',
            validate = False)

        # Add route to map with different colors
        if Path[0] == 'Distribution North':
            folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = ColorIndex_North[Counter_North]).add_to(m) 
            Counter_North += 1
        elif Path[0] == 'Distribution South':
            folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = ColorIndex_South[Counter_South]).add_to(m) 
            Counter_South += 1
        coords = []

    m.save('RouteVisuals' + os.sep + name + 'routes.html')
    return None
