import geojson
import pandas as pd
import os
import sys
import time

## Define a new class for new locations

def get_mean_point(coords):
    while len(coords[0]) != 2:
        #=======================
        if len(coords[0]) == 3: # Nasty way of settling the water catchment data
            coords = [coords[0],coords[1]]
            break
        #=======================
        coords = coords[0]
    # Check if altitude is considered

    long_mean = 0
    lat_mean = 0
    for coord in coords:
        long_mean += coord[0]
        lat_mean += coord[1]
    return long_mean/len(coords),lat_mean/len(coords)

# Python 3 program to calculate Distance Between Two Points on Earth
# Note: Distances used on Google Earth will vary with this value because
# of more accurate use of earths radius
from math import radians, cos, sin, asin, sqrt
def distance(lat1, lat2, lon1, lon2):
    
    # The math module contains a function named
    # radians which converts from degrees to radians.
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

    c = 2 * asin(sqrt(a))

    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return(c * r)

# Sort the list based on ascending order of distance
def sort_lists(lat_list,long_list,type_list,distance_list,point_type_list):
    distance_list,lat_list,long_list,type_list,point_type_list=map(list, zip(*sorted(zip(distance_list,lat_list,long_list,type_list,point_type_list))))
    return lat_list,long_list,type_list,distance_list,point_type_list


# Creating the neighbours returns a list
def create_neighbours(data,lower_limit=0,upper_limit=0.5):
    length_of_file = len(data['lat'])
    neighbours = [[]]
    for i in range(len(data['lat'])):
        ref_lat,ref_long = data['lat'][i],data['long'][i]
        for j in range(len(data['lat'])):
            if i == j:
                continue
            curr_lat,curr_long = data['lat'][j],data['long'][j]
            calculate_distance = distance(curr_lat,ref_lat,curr_long,ref_long)

            if calculate_distance > lower_limit and calculate_distance <= upper_limit:
                neighbours[i].append(j+2) # +2 because we shift it down
        if i != length_of_file-1:
            neighbours.append([])
    return neighbours

# Main will get the top n% files and then generate a csv
def main():
    if len(sys.argv) != 1 or len(sys.argv) == 6:
        ref_lat, ref_long = float(sys.argv[1]), float(sys.argv[2])
        lower_limit,upper_limit = float(sys.argv[3]),float(sys.argv[4])
        percentage = 100 // float(sys.argv[5])
    else:
        ref_lat, ref_long = 1.2833412, 103.8588642
        lower_limit,upper_limit = 0,0.5
        percentage = 20 # Defaults to 5 percent 
    onlyfiles = os.listdir()
    geojson_files = []
    for file in onlyfiles:
        if ".geojson" in file:
            geojson_files.append(file)

    temp_lat = []
    temp_long = []
    temp_type = []
    temp_distance = []
    temp_point_type = []

    data = {'name' : [], 'long' : [], 'lat' : [],'type' : [],'distance' : [],'point_type' : [], 'neighbours': []}
    for file in geojson_files:
        temp_lat = []
        temp_long = []
        temp_type = []
        temp_distance = []
        temp_point_type = []

        path_to_file = f"./{file}"
        with open(path_to_file) as f:
            gj = geojson.load(f)
        features = gj['features']
        for i in range(len(features)):
            try:
                type_of_feature = features[i]['geometry']['type']
                coords = features[i]['geometry']['coordinates']
                # For polygons
                if type_of_feature == 'Polygon' or type_of_feature == 'MultiPolygon':
                    long,lat = get_mean_point(coords)
                    temp_lat.append(lat)
                    temp_long.append(long)
                    temp_type.append(type_of_feature)
                    temp_distance.append(distance(lat,ref_lat,long,ref_long))
                    temp_point_type.append(f"{file.strip('.geojson')}")
                elif type_of_feature == 'LineString' or type_of_feature == 'MultiLineString':
                    # Line strings
                    while len(coords[0]) != 2:
                        coords = coords[0]
                    for coord in coords:
                        if coord[0] == 0 or coord[1] == 0:
                            pass
                        temp_lat.append(coord[1])
                        temp_long.append(coord[0])
                        temp_type.append(type_of_feature)
                        temp_distance.append(distance(coord[1],ref_lat,coord[0],ref_long))
                        temp_point_type.append(f"{file.strip('.geojson')}")
                else:
                    temp_lat.append(coords[1])
                    temp_long.append(coords[0])
                    temp_type.append(type_of_feature)
                    temp_distance.append(distance(coords[1],ref_lat,coords[0],ref_long))
                    temp_point_type.append(f"{file.strip('.geojson')}")
                    # points
            except Exception as e:
                continue
        
        temp_lat,temp_long,temp_type,temp_distance,temp_point_type = sort_lists(temp_lat,temp_long,temp_type,temp_distance,temp_point_type)
        max_length = int(len(temp_lat) / percentage) # Define the max length of 5% of original list
        temp_lat,temp_long,temp_type,temp_distance,temp_point_type = temp_lat[0:max_length],temp_long[0:max_length],temp_type[0:max_length],temp_distance[0:max_length],temp_point_type[0:max_length]
        
        if data['lat'] != []:
            data['long'] += temp_long.copy()
            data['lat'] += temp_lat.copy()
            data['type'] += temp_type.copy()
            data['distance'] += temp_distance.copy()
            data['point_type'] += temp_point_type.copy()
        else:
            data['long'] = temp_long.copy()
            data['lat'] = temp_lat.copy()
            data['type'] = temp_type.copy()
            data['distance'] = temp_distance.copy()
            data['point_type'] = temp_point_type.copy()
        print(data)
        neighbours = create_neighbours(data,lower_limit,upper_limit)
        data['neighbours'] = [tuple(neighbour) for neighbour in neighbours]
        print('completed')
    data['name'] = [i+2 for i in range(len(data['lat']))]
    csv_path = f"./output_{int(100 // percentage)}percent.csv"
    print(len(data['name']),len(data['long']),len(data['lat']),len(data['type']),len(data['distance']),len(data['point_type']))
    df = pd.DataFrame(data)
    df.to_csv(csv_path,index=False)


if __name__ == "__main__":
    # need reference lat, reference long, lower limit, upper limit, percentage
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Time taken to load data points = {end_time - start_time} seconds")