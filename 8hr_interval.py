import sys
from pprint import pprint
import pandas as pd


grids = pd.read_csv('grid_spec.csv')
df = pd.read_csv(sys.argv[1])

for index, row in df.iterrows():
    gid = int(grids[grids.long==row.lng][grids.lat==row.lat].Grid_ID.values[0])
    df.at[index, 'Grid_ID'] = gid

    if row.start_time < 480:
        df.at[index,'window'] = "00-08"
    elif row.start_time < 960:
        df.at[index,'window'] = "08-16"
    elif row.start_time <= 1440:
        df.at[index,'window'] = "16-24"

max_cars = {i: dict() for i in grids.Grid_ID}
for i in grids.Grid_ID:
    df_grid = df[df.Grid_ID==i]
    max_cars[i]["00-08"] = df_grid[df_grid.window=="00-08"].sum(axis=0).frcs_demand
    max_cars[i]["08-16"] = df_grid[df_grid.window=="08-16"].sum(axis=0).frcs_demand
    max_cars[i]["16-24"] = df_grid[df_grid.window=="16-24"].sum(axis=0).frcs_demand
pprint(max_cars)

max_cars_df = pd.DataFrame.from_dict(max_cars)
print(max_cars_df)