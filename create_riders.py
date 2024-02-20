from src.Grid import Grid
from src.Rider import Rider
from src.Car import Car
from src.Simulator import Simulator
from src.Order import Order, FixedOrderGenerator
import src.Utilities as Util
from typing import Dict, List
import numpy as np
import pickle
import os, sys
import yaml
from yaml.loader import SafeLoader

import time

from pprint import pprint

name = sys.argv[1]
properties_file = name+'.yml'
print(properties_file)

with open(properties_file, 'r') as stream:
    try:
        d =yaml.load(stream, Loader=SafeLoader)
    except yaml.YAMLError as e:
        print(e)

parameters = d['parameters']
data_path = "Data/" + parameters['name'] + "/"

if not os.path.exists(data_path):
    os.makedirs(data_path)
else:
    print(f"Name {parameters['name']} already used")
    exit(-1)

Map = Grid(parameters['grid_x'], parameters['grid_y'])
np.random.default_rng(parameters['seed'])


def create_random_riders(grid: Grid, number_of_riders: int, params: Dict) -> Dict[int, Rider]:
    riders: Dict[int, Rider] = dict([])
    nx, ny = grid.get_size()

    lem = params['lambda']

    previous_time = 0
    for i in range(1, number_of_riders + 1):
        ox = np.random.randint(0, nx)
        oy = np.random.randint(0, ny)
        dx = np.random.randint(0, nx)
        dy = np.random.randint(0, ny)
        if dx == ox and dy == oy:
            while dx == ox and dy == oy:
                dx = np.random.randint(0, nx)
                dy = np.random.randint(0, ny)

        # value of time from beta distribution - rounded
        value_of_time = np.round(np.random.uniform(parameters['uniform_low'], parameters['uniform_high']), 2)
        # riders in different timesteps
        t = previous_time + 1 + np.random.poisson(lem)

        riders[i] = Rider(id=i, origin=(ox, oy), destination=(dx, dy), starting_time=t, value_of_time=value_of_time)
        previous_time = t
    return riders


print("Initializing riders for experiment", parameters['name'])
for n in parameters['numbers_of_riders']:
    for i in range(1, parameters['iterations']+1):
        riders = create_random_riders(grid=Map, number_of_riders=n, params=parameters)
        riders_filename = f"riders_{len(riders)}_iter_{i}_name_{parameters['name']}"
        pickle.dump(riders, open(data_path + riders_filename, 'wb'))

print("--Riders initialized--")
