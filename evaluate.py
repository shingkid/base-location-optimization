import sys

# https://docs.python.org/3/library/queue.html
from queue import Queue

import numpy as np
import pandas as pd

from tqdm import tqdm

# import warnings
# warnings.filterwarnings("ignore")


grids = pd.read_csv('grid_spec.csv')
distances = pd.read_csv('distances.csv')
speed = [12, 20] # km/h
response_time = [0.5, 0.25] # hr

def get_bases_by_distance(location, bases, urgency):
    location -= 1 # distance matrix indexes from 0 while grids index from 1
    nearest = distances.iloc[location, :].sort_values().index
    return [int(i)+1 for i in nearest if int(i)+1 in bases and within_reach(location, int(i), urgency)]


def within_reach(a, b, urgency):
    target = speed[urgency] * response_time[urgency]
    return distances.iloc[a-1, b-1] <= target


def service_time(base, incident):
    distance = distances.iloc[base-1, int(incident.Grid_ID)-1]
    travel_time = distance / speed[int(incident.is_urgent)] * 60
    return_time = distance / speed[0] * 60
    return travel_time + incident.engagement_time + return_time


def assign_cars(df, supply):
    success = 0
    q = Queue()
    # Start timeline
    for i in tqdm(range(1440)):
        # If an incident happens
        if len(df[df.start_time==i]) > 0:
            t = df[df.start_time==i] # All incidences at time i
            # TODO: Attempt to handle those in queue
            for index, row in t.iterrows():
                # Get list of bases in order of distance
                nearest_bases = get_bases_by_distance(int(row.Grid_ID), supply.keys(), int(row.is_urgent))
                demand = row.frcs_demand

                for b in nearest_bases:
                    # If base has available car
                    if 0 in supply[b]:
                        demand -= 1
                        car = supply[b].index(0)
                        supply[b][car] = service_time(b, row)

                    # Stop looking if incident has been handled
                    if demand == 0:
                        success += 1
                        break
                
                # If incident couldn't be handled, add to queue
                if demand==row.frcs_demand:
                # if demand > 0:
                    q.put(row)

        # Decrement from all car times
        for k, v in supply.items():
            supply[k] = [max(0, x-1) for x in v]

        # print(supply)

    failures = q.qsize()
    return (len(df)-success)/len(df)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        exit()

    filename = sys.argv[1]
    sol_file = sys.argv[2]
    df = pd.read_csv(filename, index_col='id').sort_values(by=['start_time'])
    allocation = pd.read_csv(sol_file)

    supply = {int(row.Grid_ID): [0]*int(row.frc_supply) for index, row in allocation.iterrows()}

    for index, row in df.iterrows():
        gid = int(grids[grids.long==row.lng][grids.lat==row.lat].Grid_ID.values[0])
        df.at[index, 'Grid_ID'] = gid

    risk = assign_cars(df, supply)

    print("Risk: " + str(risk*100) + "%")