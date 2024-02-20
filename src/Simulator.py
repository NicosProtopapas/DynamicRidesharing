from typing import Dict, List, Tuple
from src.Grid import Grid
from src.Rider import Rider
from numpy import random

from tqdm import tqdm
import pandas as pd
from src.Car import Car


class CarCannotExistError(Exception):
    """Raised when a rider is assigned to impossible car (0)"""
    pass


class Simulator(object):
    """
        A general simulation class
    """

    def __init__(self, grid: Grid, riders: Dict[int, Rider], depot_locations: Dict[int, Tuple], seed: int,
                 maximum_number_of_cars: int, cost: Tuple, capacity: Tuple) -> None:
        self.number_of_riders: int = None
        self.grid: Grid = grid
        self.riders: Dict[int, Rider] = riders
        self.depot_locations: Dict[int, Tuple] = depot_locations
        self.starting_times_index = dict([])
        self.cars_counter = 0
        self.cars: Dict[int, Car] = dict()
        self.deactivated_cars = dict()
        self.cars_counter = 0
        if cost[0] == "Fixed":
            self.car_cost_flag = "Fixed"
            self.fixed_car_cost = cost[1]
        else:
            self.car_cost_flag = "Random"
            self.cost_lower_bound = cost[1][0]
            self.cost_upper_bound = cost[1][1]
        if capacity[0] == "Fixed":
            self.car_capacity_flag = "Fixed"
            self.car_capacity = capacity[1]
        else:
            self.car_capacity_flag = "Random"
            self.car_capacity_pool = capacity[1]['pool']
            self.car_capacity_probabilities = capacity[1]['probabilities']
        self.maximum_number_of_cars = maximum_number_of_cars
        self.seed = seed

    def preprocessing(self, verbose=True):
        self.number_of_riders = len(self.riders)
        for i in self.riders:
            time = self.riders[i].starting_time
            if time in self.starting_times_index:
                self.starting_times_index[time].append(i)
            else:
                self.starting_times_index[time] = [i]
        if verbose:
            print("Pre-processing finished: Simulation with", self.number_of_riders, "riders ready to start!")
            print(f"Grid size: {self.grid.get_size()}")
            print("Depots:\n")
            for depot_id in self.depot_locations:
                print(f'depot {depot_id} at {self.depot_locations[depot_id]}')
            print("Maximum number of cars", self.maximum_number_of_cars)
            print("-----")

    def simulate(self, method: str, verbose=False, debug=False, silent=False):
        """
        The main simulation function.
        First, the new rider is examined, and allocated into cars
        Then, the cars check whether they need to pick-up or drop-off any rider
        Then move to next location

        :param debug:
        :param method: method used for proposing new routes
        :param verbose: flag for printing non-essential messages
        :param debug: extensive printing for debugging purposes
        :param silent: minimal printing, has priority over verbose and debug
        :return:
        """

        if silent:
            verbose = False
            debug = False

        timer: int = 0

        while any(self.riders[i].finished is False for i in self.riders):
            finished = sum([self.riders[i].finished for i in self.riders])
            if not silent:
                print(f" {finished} out of {self.number_of_riders} riders, finished by time {timer}")
            if verbose:
                print("time", timer)

            # disembark passengers which are in their destination
            for car_id in self.cars:
                self.cars[car_id].remove_passengers(timer, verbose=verbose, debug=debug)

            if timer in self.starting_times_index:

                for new_rider_id in self.starting_times_index[timer]:
                    new_rider: Rider = self.riders[new_rider_id]
                    new_rider.init()
                    if not silent:
                        print()
                        print("RIDER", new_rider_id)
                        print()
                        self.riders[new_rider_id].print_quick_details()
                    car_locations = [self.cars[i].current_location for i in self.cars]
                    self.riders[new_rider_id].set_optimal_travelling_time(self.grid, self.depot_locations.values(),
                                                                          car_locations)

                    # Car proposals by in-route cars
                    temporary_selection: int = 0  # temporary selection by the rider. 0 means not allocated
                    temporary_utility: float = float('-inf')

                    for car_id in self.cars:
                        if len(self.cars[car_id].passengers) < self.number_of_riders:

                            # pruning: if utility cannot be better than current utility, even 0 payment, no need to examine

                            best_case_finishing_time = self.grid.shortest_path(self.cars[car_id].current_location,
                                                                               new_rider.origin) + self.grid.shortest_path(
                                new_rider.origin, new_rider.destination)
                            if not silent:
                                print("best case- time", best_case_finishing_time, "utility",
                                      new_rider.utility(best_case_finishing_time + timer, 0))
                            if new_rider.utility(best_case_finishing_time + timer, 0) < temporary_utility:
                                if not silent:
                                    print("car ", car_id, "is pruned")

                            if method == "externalities":
                                new_proposal_tuple = self.cars[car_id].propose_route_with_externalities(new_rider,
                                                                                                        self.grid,
                                                                                                        timer,
                                                                                                        debug=False,
                                                                                                        verbose=verbose)
                            elif method == "fixed_discount":
                                new_proposal_tuple = self.cars[car_id].propose_route_fixed_discount(new_rider,
                                                                                                    self.grid, timer,
                                                                                                    debug=False,
                                                                                                    verbose=verbose)
                            elif method == "fifo":
                                new_proposal_tuple = self.cars[car_id].propose_route_fifo(new_rider, self.grid, timer,
                                                                                          debug=False, verbose=verbose)
                            else:
                                print("undefined method")
                                exit(1)

                            if new_proposal_tuple[0] > 0:
                                # no feasible route is possible
                                if verbose:
                                    print("car", car_id, new_proposal_tuple[1])
                                continue  # check the next car
                            else:
                                new_proposal = new_proposal_tuple[1]

                            proposed_finishing_time = new_proposal["finishing time"]
                            proposed_payment = new_proposal["payment"]

                            if new_rider.utility(proposed_finishing_time, proposed_payment) >= temporary_utility:
                                temporary_utility = new_rider.utility(proposed_finishing_time, proposed_payment)
                                temporary_selection = car_id
                                selected_proposal = new_proposal

                            if not silent:
                                print(f'proposal by car {car_id}')
                                print(new_proposal)

                    if self.cars_counter < self.maximum_number_of_cars:
                        for depot_id in self.depot_locations:
                            if self.car_cost_flag == "Fixed":
                                cost = self.fixed_car_cost
                            elif self.car_cost_flag == "Random":
                                cost = random.uniform(self.cost_lower_bound,self.cost_upper_bound)

                            if self.car_capacity_flag == "Fixed":
                                capacity = self.car_capacity
                            else:
                                capacity = random.choice(self.car_capacity_pool, 1, False, p=self.car_capacity_probabilities)
                            temp_new_car: Car = Car(-depot_id, capacity, cost,
                                                    self.depot_locations[depot_id], self.depot_locations[depot_id],
                                                    timer)
                            if method == "externalities":
                                new_proposal_tuple = temp_new_car.propose_route_with_externalities(new_rider, self.grid,
                                                                                                   timer, debug=False,
                                                                                                   verbose=verbose)
                            elif method == "fixed_discount":
                                new_proposal_tuple = temp_new_car.propose_route_fixed_discount(new_rider, self.grid,
                                                                                               timer, debug=False,
                                                                                               verbose=verbose)
                            elif method == "fifo":
                                new_proposal_tuple = temp_new_car.propose_route_fifo(new_rider, self.grid, timer,
                                                                                     debug=False, verbose=verbose)
                            else:
                                print("undefined method")
                                exit(2)

                            if new_proposal_tuple[0] > 0:
                                if verbose:
                                    print("depot", depot_id, new_proposal_tuple[1])
                                continue
                            else:
                                new_proposal = new_proposal_tuple[1]
                            proposed_finishing_time = new_proposal["finishing time"]
                            proposed_payment = new_proposal["payment"]

                            if not silent:
                                print(f'proposal by depot {depot_id}')
                                print(new_proposal)

                            if new_rider.utility(proposed_finishing_time, proposed_payment) > temporary_utility:
                                temporary_utility = new_rider.utility(proposed_finishing_time, proposed_payment)
                                temporary_selection = -depot_id
                                selected_proposal = new_proposal
                                temp_selected_car = temp_new_car
                            if verbose:
                                print(f'\t New car from depot {depot_id} proposed utility: {temporary_utility} ')

                    try:
                        if temporary_selection > 0:
                            rider_selected_car = temporary_selection

                        if temporary_selection < 0:
                            # a new car is created from depot in temporary selected car
                            self.cars_counter = len(self.cars)
                            self.cars_counter += 1
                            new_car_depot: int = -temporary_selection
                            new_car_depot_location: Tuple = self.depot_locations[new_car_depot]
                            temp_new_car = temp_selected_car
                            """
                            temp_new_car: Car = Car(self.cars_counter, self.car_capacity, cost,
                                                    new_car_depot_location, new_car_depot_location,
                                                    timer)
                            """
                            self.cars[self.cars_counter] = temp_new_car
                            rider_selected_car = self.cars_counter

                        if temporary_selection == 0:
                            raise CarCannotExistError
                    except CarCannotExistError:
                        print("Rider selects a non-existant car! Check the code!")
                        exit(1)

                    if debug:
                        print("selected car", rider_selected_car)

                    if "compensations" in selected_proposal:
                        compensations = selected_proposal["compensations"]
                    else:
                        compensations = dict()
                    route_order = selected_proposal["order"]
                    route = selected_proposal["location order"]
                    proposed_payment = selected_proposal["payment"]
                    proposed_finishing_time = selected_proposal["finishing time"]
                    self.cars[rider_selected_car].allocate_passenger(new_rider, route_order, self.grid, debug=False)
                    new_rider.allocate_rider(rider_selected_car, proposed_finishing_time, proposed_payment,
                                             compensations, route_order, route)

                    # distribute compensations
                    for i in compensations:
                        self.cars[rider_selected_car].passengers[i].compensations_in[new_rider.id] = compensations[i]

                    history_dict = {
                        "new rider": new_rider_id,
                        "current location": self.cars[rider_selected_car].current_location,
                        "route": route,
                        "order": route_order,
                        "passengers": [i for i in self.cars[rider_selected_car].passengers],
                        "finishing times": selected_proposal["finishing times"]
                    }
                    self.cars[rider_selected_car].history[timer] = history_dict

                    if verbose:
                        print(
                            f'rider {new_rider_id} is allocated in car {rider_selected_car}, with order {route_order}\n locations: {route}')
                        print(f' car {rider_selected_car} follows path {self.cars[rider_selected_car].current_path}')

            # embark passengers
            for car_id in self.cars:
                self.cars[car_id].embark_passengers(timer, verbose=verbose, debug=False)

            # update_location
            for car in self.cars:
                if not silent:
                    print("car trace: car", car, "time", timer, "loc:", self.cars[car].current_location,
                          "allocated passenger list", self.cars[car].allocated_passengers_list(),
                          "travelling passenger list", self.cars[car].travelling_passengers_list())
                for rider_id in self.cars[car].passengers:
                    self.riders[rider_id].trace_locations(self.cars[car].current_location, timer)
                    flag = self.riders[rider_id].check_if_stopped(self.cars[car].current_location)
                    if flag == 1:
                        print(self.cars[self.riders[rider_id].allocated_car])

                self.cars[car].update_location(timer)
                self.cars[car].update_metrics()

            for i in self.riders:
                self.riders[i].update_metrics()

            timer = timer + 1
