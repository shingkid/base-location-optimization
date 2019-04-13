import csv
import json
from math import radians, cos, sin, asin, sqrt
import os
from pprint import pprint
import sys
import time

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

from tqdm import tqdm

from docplex.mp.model import Model

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def compute_distances():
    locations = pd.read_csv('grid_spec_for_students.csv', index_col='Grid_ID')
    loc_arr = locations.values
    distances = pd.DataFrame()
    for i in range(len(loc_arr)):
        lon1 = loc_arr[i][0]
        lat1 = loc_arr[i][1]
        for j in range(len(loc_arr)):
            lon2 = loc_arr[j][0]
            lat2 = loc_arr[j][1]
            distances.at[i,j]  = haversine(lon1, lat1, lon2, lat2)
    
    return distances

def compute_adj_mat(distances, radius):
    adj_matrix = []
    for index, row in distances.iterrows():
        can_reach = [int(x) for x in list(np.where(row<=radius)[0])]
        adj_matrix.append(can_reach)
    return adj_matrix

def find_min_bases(adj_matrix):
    adj_matrix = pd.DataFrame(adj_matrix)
    nlocs = 365
    mdl = Model()

    # Decision variables
    x_j = {}
    for j in range(nlocs):
        x_j[j] = mdl.binary_var(name='x[%d]' % j)

    # Objective function
    obj = mdl.linear_expr()
    for j in range(nlocs):
        obj.add(x_j[j])
    mdl.minimize(obj)

    # Constraints
    for index, row in adj_matrix.iterrows():
        cnst = mdl.linear_expr()
        for i in row:
            if not np.isnan(i):
                cnst.add(x_j[i])
        mdl.add_constraint(cnst >= 1, 'Grid %d' % (index+1))

    # Solve
    bases = []
    try:
        mdl.solve()
        print(mdl.get_solve_details())
        print('obj_val = %d' % mdl.objective_value)
        for j in range(nlocs):
            if x_j[j].solution_value == 1:
                bases.append(j+1)
    except:
        print('Model not solved :(')
        print(mdl.get_solve_details())
    
    return bases

def load_data(DATA_DIR, grids, regions, distances, day):
    # Read from CSV file
    filename = os.path.join(DATA_DIR, 'full_sample_%d_for_students.csv' % day)
    df = pd.read_csv(filename, index_col='id')

    for index, row in df.iterrows():
        # Match lat long to Grid_ID
        gid = int(grids[grids.long==row.lng][grids.lat==row.lat].Grid_ID.values[0])
        df.at[index, 'Grid_ID'] = gid

        # Assign nearest base
        best_base = None
        shortest_distance = 100
        for base, grid_list in regions.items():
            if gid in grid_list:
                base = int(base)
                d = distances.iloc[gid, base]
                if d < shortest_distance:
                    shortest_distance = d
                    best_base = base
                
        df.at[index, 'spf_base'] = best_base
        df.at[index, 'distance'] = shortest_distance

        # Calculate travel time and end time
        speed = [12, 20]
        travel_time = shortest_distance / speed[int(row.is_urgent)] * 60
        return_time = shortest_distance / speed[0] * 60
        df.at[index, 'travel_time'] = travel_time
        df.at[index, 'end_time'] = row.start_time + travel_time + row.engagement_time + return_time # TODO: Check if cross to next day

    # df.to_csv("day%d.csv" % day, index=False)

    return df

def load_dataset(DATA_DIR, DATA_FILES, grids, regions, distances, day=None):
    if day != None:
        # print("single day")
        return load_data(DATA_DIR, grids, regions, distances, day)

    df = pd.DataFrame()
    i = 0
    weekday = -1
    for i in range(len(DATA_FILES)): # 90 days of data
        day_df = load_data(DATA_DIR, grids, regions, distances, i)
        day_df['day'] = i

        weekday += 1
        if weekday > 6:
            weekday = 0
        day_df['weekday'] = weekday

        df = df.append(day_df)

    # df.to_csv("incidences.csv", index=False)

    return df

def find_worst_day_by_grid(df, grids):
    worst_days = []
    for i in grids.Grid_ID:
        df_grid = df[df.Grid_ID==i]
        worst = 0
        worst_day = None
        for d in list(df_grid.day):
            day_total = df_grid[df_grid.day==d].sum(axis=0).frcs_demand
            if day_total > worst:
                worst = day_total
                worst_day = d
        worst_days.append({"day": worst_day, "total_cars": worst})
    return worst_days

def get_worst_day_incidences(df, grids, worst_days):
    incidences = pd.DataFrame()
    
    for i in grids.Grid_ID:
        wd = worst_days[i-1]
        grid_incidences = df[df.Grid_ID == i]
        wd_grid_incidences = grid_incidences[grid_incidences.day == wd['day']]
        wd_grid_incidences.sort_values(by=['start_time'])
        if len(wd_grid_incidences) > 0:
            incidences = incidences.append(wd_grid_incidences)
    
    incidences.reset_index(inplace=True)
    incidences.rename(columns={'index':'incidence_id'}, inplace=True)
    # incidences.to_csv("worst_day.csv", index=False)
    return incidences

def find_average_incidences_by_grid(df, grids):
    random_state = 6
    incidences = pd.DataFrame()

    for i in grids.Grid_ID:
        grid_incidences = df[df.Grid_ID == i]
        avg = round(len(grid_incidences) / len(DATA_FILES))
        print(avg)
        sample = grid_incidences.sample(n=avg, random_state=random_state)
        print(len(sample))
        incidences = incidences.append(sample)

    incidences.reset_index(inplace=True)
    incidences.rename(columns={'index':'incidence_id'}, inplace=True)
    # incidences.to_csv("average.csv", index=False)
    return incidences

def overlap(start1, end1, start2, end2):
    return start1 <= start2 and start2 < end1 or start2 <= start1 and start1 < end2

def find_clashes(incidences):
    clashes = pd.DataFrame()

    for index, row in tqdm(incidences.iterrows()):
        for index2, row2 in incidences.iterrows():
            conflict = overlap(row.start_time, row.end_time, row2.start_time, row2.end_time)
            if row.spf_base != row2.spf_base:
                conflict = True
                
            clashes.at[index, index2] = conflict
    
    return clashes

def allocate(assigned_bases, clashes, num_cars=15):
    mdl = Model()

    I = len(assigned_bases.index) #number of tasks
    J = num_cars #number of cars
    # K =  6 #number of base stations

    # Decision variables
    x_ij = {}
    # y_jk = {}
    # z_ik = pd.read_csv('incident_2.csv')
    for i in range(I):
        for j in range(J):
            x_ij[i, j] = mdl.binary_var(name='x[%d,%d]' % (i, j))

    # y_jk = {}
    # for j in range(I):
        # for k in range(J):
            # y_jk[j, k] = mdl.binary_var(name='y[%d,%d]' % (j, k))


    # Objective function
    obj = mdl.linear_expr()
    for i in range(I):
        for j in range(J):
                obj.add(x_ij[i, j])
    mdl.maximize(obj)

    # Constraints
    #for all tasks, sum of Xij can only be less than or equal to 1
    for i in range(I):
        cnst = mdl.linear_expr()
        for j in range(J):
            cnst.add(x_ij[i, j])
        mdl.add_constraint(cnst <= 1, 'I[%d]' % i)

    #constraints for clashes, same car cannot attend to incidents that clash
    for j in range (J):    
        for k in range (I):
            for i in range (k+1, I):
                if clashes.iloc[k, i]:
                    cnst = mdl.linear_expr()
                    cnst.add(x_ij[k, j])
                    cnst.add(x_ij[i, j])
                    mdl.add_constraint(cnst <= 1, 'Clash %d' % (I+1))

    # Solve
    hash = {}
    try:
        mdl.solve()
        print(mdl.get_solve_details())
        print('obj_val = %d' % mdl.objective_value)
        for i in range(I):
            for j in range(J):
                print('x[%d,%d] = %d' % (i, j, x_ij[i, j].solution_value))
                if x_ij[i, j].solution_value == 1:
                    base = int(assigned_bases.iloc[i])
                    if base in hash:
                        hash[base].add(j)
                    else:
                        hash[base] = {j, }
        
        
        # Write to file
        with open('sol.csv', 'w') as out:
            row1 = "lng" + "," + "lat" + "," + "frc_supply\n"
            out.write(row1)
            for key, v in hash.items():
                row = str(grids.iloc[key-1, 1]) + "," + str(grids.iloc[key-1, 2]) + "," + str(len(v)) + "\n"
                out.write(row)

    except:
        print('Model not solved :(')
        print(mdl.get_solve_details())

if __name__ == "__main__":
    nargs = len(sys.argv)
    if nargs < 4:
        sys.exit(1)
    # else:
    #     print(sys.argv)

    t0 = time.time()

    DATA_DIR = sys.argv[1]
    DATA_FILES = os.listdir(DATA_DIR)
    radius = float(sys.argv[2])

    print("Loading grid specs...")
    grids = pd.read_csv('grid_spec.csv')
    print("Loading distance matrix...")
    # distances = compute_distances()
    distances = pd.read_csv('distances.csv')

    print("Computing adjacency matrix...")
    adj_mat = compute_adj_mat(distances, radius)

    print("Solving minimum bases required...")
    base_list = find_min_bases(adj_mat)

    print("Calculating grids covered by each base...")
    regions = {}
    for i in base_list:
        # print(adj_mat[i-1])
        regions[i] = adj_mat[i-1]

    # pprint(regions)

    day = sys.argv[3]
    try:
        day = int(day)
        print("Loading day %d data..." % day)
        df = load_dataset(DATA_DIR, DATA_FILES, grids, regions, distances, day) # Load specific day
    except ValueError:
        print("Loading all incidences...")
        df = load_dataset(DATA_DIR, DATA_FILES, grids, regions, distances) # Load all data
        day = sys.argv[3]
        print("Getting incidences for %s day..." % day)
        if day == "worst":
            worst_days = find_worst_day_by_grid(df, grids)
            # print(worst_days)
            df = get_worst_day_incidences(df, grids, worst_days)
        elif day == "average":
            df = find_average_incidences_by_grid(df, grids)

    # print(df)

    print("Finding overlaps in incidence times...")
    clashes = find_clashes(df)
    # print(clashes)

    print("Solving...")
    if nargs == 5:
        num_cars = int(sys.argv[4])
        allocate(df.spf_base, clashes, num_cars)
    else:
        allocate(df.spf_base, clashes)

    print("Time taken:", time.time() - t0)
