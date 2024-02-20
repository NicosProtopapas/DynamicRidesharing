import copy
from src.Grid import Grid
from src.Simulator import Simulator
from tqdm import tqdm
from typing import Dict, List
import numpy as np
import pickle
import yaml
import os
import sys
from yaml.loader import SafeLoader

import time

from pprint import pprint

name = sys.argv[1]
properties_file = name+'.yml'
with open(properties_file, 'r') as stream:
    try:
        d =yaml.load(stream, Loader=SafeLoader)
    except yaml.YAMLError as e:
        print(e)

parameters = d['parameters']
results_path = "Results/" + parameters['name'] + "/"
data_path = "Data/" + parameters['name'] + "/"

if not os.path.exists(results_path):
    os.makedirs(results_path)
else:
    print(f"Name {parameters['name']} already used")
    exit(-1)


Map = Grid(parameters['grid_x'], parameters['grid_y'])
np.random.default_rng(parameters['seed'])

def run_simulation(params: Dict, data_path: str,  results_path : str, verbose=False):

    with open(results_path+"params.yml", 'w') as file:
        yaml.dump(params, file)

    for n in parameters['numbers_of_riders']:
        for iteration in tqdm(range(1, params['iterations']+1)):
            riders_filename = f"riders_{n}_iter_{iteration}_name_{params['name']}"
            riders = pickle.load(open(data_path + riders_filename, 'rb'))

            # create random depots
            depot_locations = dict([])
            for dep in range(1, params['number_of_depots'] + 1):
                temp = (np.random.randint(0, parameters['grid_x']), np.random.randint(0, parameters['grid_y']))
                if temp not in depot_locations.values():
                    depot_locations[dep] = temp


            methods = ["externalities", "fifo", "fixed_discount"]

            for method in methods:
                riders_to_sim = copy.deepcopy(riders)

                sim = Simulator(
                                grid=Map, riders=riders_to_sim,
                                depot_locations=depot_locations,
                                seed=params['seed'],
                                maximum_number_of_cars=params['maximum_number_of_cars'],
                                cost=(params['cost_flag'], params['cost']),
                                capacity=(params['capacity_flag'], params['capacity'])
                                )
                sim.preprocessing()
                sim.simulate(method, verbose=verbose, silent=True)
                filename_cars = f"new_rider_{n}_iter_{iteration}_name_{params['name']}_{method}_cars"
                filename_riders = f"new_rider_{n}_iter_{iteration}_name_{params['name']}_{method}_riders"
                pickle.dump(sim.cars, open(results_path + filename_cars, 'wb'))
                pickle.dump(sim.riders, open(results_path + filename_riders, 'wb'))

start_time = time.time()
print("parameters", parameters)
run_simulation(params=parameters, data_path=data_path, results_path=results_path, verbose=False)
print("--- %s seconds ---" % (time.time() - start_time))
