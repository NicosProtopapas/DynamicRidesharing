from src.Rider import Rider
from src.Car import Car
import pickle
from poverty import gini
from tqdm import tqdm
import pandas as pd
import seaborn as sns
sns.set_theme(style="ticks", palette="pastel")
import yaml
import os
import sys
from yaml.loader import SafeLoader
import numpy as np

import matplotlib.pyplot as plt


name = sys.argv[1]
properties_file = name+'.yml'
with open(properties_file, 'r') as stream:
    try:
        d =yaml.load(stream, Loader=SafeLoader)
    except yaml.YAMLError as e:
        print(e)

parameters = d['parameters']
folder = "Results/" + parameters['name'] + "/"

if not os.path.exists("Output/"+ parameters['name']):
    os.makedirs("Output/"+ parameters['name'])

labels = ['number of riders','iteration', 'method', 'id',
          'direct time',
          'proposed usage time',
          'ex-post usage time',
          'optimal usage time',
          'proposed - expost',
          'proposed - optimal',
          'proposed utility',
          'expost utility',
          'expost - proposed utility',
          'payment'
          ]

list_two_labels = [
    'number of riders', 'iteration', 'method',
    'mean optimal commute time',
    'mean proposed commute time',
    'mean ex-post commute time',
    'mean proposed utility',
    'mean ex-post utility',
    'gini proposed utility',
    'gini ex-post utility',
    'minimum proposed utility',
    'minimum ex-post utility',
    'utility ex-post vs proposed',
    'commute time ex-post vs proposed',
    'mean direct time'
]

car_labels = ['number of riders', 'iteration', 'method',
              'travelling time',
              'mean used seats',
              'mean used seats while allocated',
              'mean empty seats',
              'mean empty seats while allocated',
              ]

car_labels_two = [ 'number of riders', 'iteration', 'method',
                    'total travelling time',
                    'total travelling time normalized',
                    'total used seats',
                    'total used seats while allocated'
                    'mean empty seats',
                    'mean empty seats while allocated'
                   ]

methods = ["externalities", "fifo", "fixed_discount"]
method_map = {"externalities": "Comp.", "fifo" : "FIFO", "fixed_discount": "Disc."}

numbers_of_riders = parameters['numbers_of_riders']

data_list = []
data_list_two = []
data_list_two_car = []


for number_of_riders in tqdm(numbers_of_riders):
    for iteration in range(1, parameters['iterations']+1):
        for method in methods:
            name =parameters['name']
            filename_cars = f"new_rider_{number_of_riders}_iter_{iteration}_name_{name}_{method}_cars"
            filename_riders = f"new_rider_{number_of_riders}_iter_{iteration}_name_{name}_{method}_riders"
            riders = pickle.load(open(folder + filename_riders, 'rb'))
            cars = pickle.load(open(folder + filename_cars, 'rb'))

            sum_of_opt_times = 0
            sum_of_proposed_usage_times = 0
            sum_of_ex_post_usage_times = 0
            sum_of_direct_times = 0
            proposed_utilities = []
            ex_post_utilities = []

            for rider_id in riders:
                current_rider: Rider = riders[rider_id]

                data_row = [
                    number_of_riders, iteration, method_map[method], current_rider.id,
                    current_rider.proposed_finishing_time - current_rider.starting_time,
                    current_rider.ex_post_finishing_time - current_rider.starting_time,
                    current_rider.optimal_travelling_time,
                    (
                                -current_rider.proposed_finishing_time + current_rider.ex_post_finishing_time) / current_rider.proposed_finishing_time,
                    ((
                                 current_rider.proposed_finishing_time - current_rider.starting_time) - current_rider.optimal_travelling_time) / current_rider.optimal_travelling_time,
                    current_rider.proposed_utility,
                    current_rider.utility(current_rider.ex_post_finishing_time, current_rider.proposed_payment),
                    current_rider.ex_post_utility - current_rider.proposed_utility,
                    current_rider.proposed_payment
                ]

                sum_of_opt_times += current_rider.optimal_travelling_time
                sum_of_proposed_usage_times += (current_rider.proposed_finishing_time - current_rider.starting_time)
                sum_of_ex_post_usage_times += (current_rider.ex_post_finishing_time - current_rider.starting_time)
                proposed_utilities.append(current_rider.proposed_utility)
                ex_post_utilities.append(current_rider.ex_post_utility)
                sum_of_direct_times += current_rider.direct_route_time

                data_row = dict(zip(labels, data_row))
                data_list.append(data_row)

            data_row_two = [
                number_of_riders, iteration, method_map[method],
                sum_of_opt_times / number_of_riders,
                sum_of_proposed_usage_times / number_of_riders,
                sum_of_ex_post_usage_times / number_of_riders,
                sum_of_ex_post_usage_times / number_of_riders,
                sum(proposed_utilities) / number_of_riders,
                sum(ex_post_utilities) / number_of_riders,
                gini([-u for u in proposed_utilities]),
                gini([-u for u in ex_post_utilities]),
                min([u for u in proposed_utilities]),
                min([u for u in ex_post_utilities]),
                sum(ex_post_utilities) / sum(proposed_utilities),
                sum_of_ex_post_usage_times / sum_of_proposed_usage_times,
                sum_of_direct_times/number_of_riders
            ]

            data_row_two = dict(zip(list_two_labels, data_row_two))
            data_list_two.append(data_row_two)

            total_travelling_time = 0
            total_used_seats = 0
            total_used_seats_while_allocated = 0

            for car_id in cars:
                current_car: Car = cars[car_id]

                data_row_car = [
                    number_of_riders, iteration, method_map[method], current_car.id,
                    current_car.travelling_time,
                    sum(current_car.used_seats) / current_car.travelling_time,
                    sum(current_car.used_seats_while_allocated) / current_car.allocated_time,
                    current_car.non_allocated_time
                ]
                total_travelling_time += current_car.travelling_time
                total_used_seats += sum(current_car.used_seats) / current_car.travelling_time
                total_used_seats_while_allocated += sum(current_car.used_seats_while_allocated) / current_car.allocated_time
                total_empty_seats = sum(current_car.capacity - np.array(current_car.used_seats))/ current_car.travelling_time
                total_empty_seats_while_allocated = sum(current_car.capacity - np.array(current_car.used_seats))/ current_car.allocated_time

            data_row_car_two = [
                    number_of_riders, iteration, method_map[method],
                    total_travelling_time,
                    total_travelling_time/number_of_riders,
                    total_used_seats,
                    total_used_seats_while_allocated,
                    total_empty_seats,
                    total_empty_seats_while_allocated
            ]


            data_row_two_car = dict(zip(car_labels_two, data_row_car_two))
            data_list_two_car.append(data_row_two_car)
df_two = pd.DataFrame(data_list_two)
df_two_car = pd.DataFrame(data_list_two_car)


to_plot = [
    'mean optimal commute time',
    'mean proposed commute time',
    'mean ex-post commute time',
    'mean proposed utility',
    'mean ex-post utility',
    'gini proposed utility',
    'gini ex-post utility',
    'minimum proposed utility',
    'minimum ex-post utility',
    'utility ex-post vs proposed',
    'commute time ex-post vs proposed',
    'mean direct time'
]


for y in to_plot:
    sns.lineplot(x="number of riders", y=y,  data=df_two, marker=True, hue = "method")

    plt.savefig("Output/"+ parameters['name']+"/"+ y + ".pdf")
    plt.close()

sns.lineplot(x="number of riders", y="mean empty seats while allocated",  data=df_two_car, marker=True, hue = "method")
plt.savefig("Output/"+ parameters['name']+"/"+ "mean empty seats while allocated" + ".pdf")
plt.close()

sns.lineplot(x="number of riders", y="total travelling time normalized",  data=df_two_car, marker=True, hue = "method")
plt.savefig("Output/"+ parameters['name']+"/"+ "total travelling time normalized" + ".pdf")


df_two.to_csv("Output/"+ parameters['name']+"/"+"output_riders.csv")
df_two_car.to_csv("Output/"+ parameters['name']+"/"+"output_cars.csv")
