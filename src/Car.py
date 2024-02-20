import numpy as np

from src.Grid import Grid
from src.Rider import Rider
from src.Order import Order, FixedOrderGenerator
import src.Utilities as Util
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass, field
from pprint import pprint
import networkx as nx
import pandas as pd

import copy


@dataclass
class Car:
    """
    Class for describing the vehicles.
    """

    id: int
    capacity: int
    cost: int
    current_location: Tuple
    depot_location: Tuple
    creation_time: int

    passengers: Dict[int, Rider] = field(default_factory=lambda: dict([]))
    passengers_travelling_times: Dict = field(default_factory=lambda: dict([]))
    current_shortest_paths: Dict = field(default_factory=lambda: dict([]))
    # path to the next location
    current_path: List = field(default_factory=lambda: [])
    current_location_order: List = field(default_factory=lambda: [])
    current_order: Tuple[Tuple] = field(default_factory=lambda: [])
    current_partial_order: List[Tuple] = field(default_factory=lambda: [])
    following_rider_id: int = -1  # -1 mean no rider is set yet
    following_rider_status: int = 'u'  # u: unknown, o: origin, 'd':des"tination
    following_order_part: Tuple = ()
    en_route: bool = True
    travelling_time: int = 0
    total_time: int = 0
    used_seats: List = field(default_factory=lambda: [])
    used_seats_while_allocated: List = field(default_factory=lambda: [])
    non_allocated_time: int = 0
    allocated_time: int = 0
    empty_seats: int = 0
    empty_seats_while_travelling: int = 0
    history: Dict = field(default_factory=lambda: dict([]))
    historical_path: Dict = field(default_factory=lambda: dict([]))


    def update_metrics(self):
        if self.en_route:
            self.travelling_time += 1
            self.used_seats.append(
                len([rider for rider in self.passengers if self.passengers[rider].travelling == True]))
            if len(self.passengers) == 0:
                self.non_allocated_time += 1
            else:
                self.used_seats_while_allocated.append(
                    len([rider for rider in self.passengers if self.passengers[rider].travelling == True]))
                self.allocated_time += 1

    def print_metrics(self):
        print(" ")
        print("metrics for car:", self.id)
        print("total travelling time", self.travelling_time)
        print("used seats", self.used_seats)
        print("mean used seats", sum(self.used_seats) / self.travelling_time)
        print("len of list", len(self.used_seats))
        print("returning time", self.non_allocated_time)
        print("mean used seats while allocated", sum(self.used_seats_while_allocated) / self.allocated_time)

    def print_info(self):
        print()
        print("car id", self.id)
        print("creation time", self.creation_time)
        print("passengers:", self.passengers.keys())
        print("current order:", self.current_order)
        print("current location:", self.current_location)
        print("current path:", self.current_path)

    def update_location(self, time: int):
        self.historical_path[time] = self.current_location
        if len(self.current_path) > 0:
            self.current_location = self.current_path.pop(0)

    def add_passenger(self, passenger):
        """
        add a single rider. Used only for building perposes
        """
        passenger.allocated = True
        passenger.allocated_car = self.id
        self.passengers[passenger.id] = passenger

    def allocated_passengers_list(self):
        return [i for i in self.passengers]

    def travelling_passengers_list(self):
        return [i for i in self.passengers if self.passengers[i].travelling == True ]


    def allocate_passenger(self, passenger: Rider, order: Tuple, grid: Grid, debug: bool = False):
        """
        Allocate a rider to a car.
        The rider enter the allocated list;
        the car gets a new route (i.e., order and path).
        """

        passenger.allocated = True
        passenger.allocated_car = self.id
        self.passengers[passenger.id] = passenger

        self.current_order = order
        self.current_partial_order = list(order)
        location_order = self.order_to_locations(self.current_order, passenger)
        if debug:
            print(len(self.passengers))
            print("order", order)
            print("self.order", self.current_order)
            print("locations", location_order)

        new_path = []
        for i in range(1, len(location_order)):
            location = location_order[i]
            temp: Tuple = grid.shortest_path(location_order[i - 1], location_order[i], include_path=True)
            path_to_next_location: List = temp[1]
            path_to_next_location.pop(0)
            new_path = new_path + path_to_next_location
            self.current_path = new_path

            if debug:
                print("location", i, ":", location_order[i])
                print("path between ", location_order[i - 1], location_order[i])

                print("current location", self.current_location)
                print("location order", location_order)
                print("path to location", path_to_next_location)
                print("new_path", new_path)

    def embark_passengers(self, timer: int, verbose=False, debug=False):
        embarkation_candidates = set()
        for passenger_id in self.passengers:
            if self.passengers[passenger_id].travelling is False:
                if debug:
                    print("embark", passenger_id, "at", self.passengers[passenger_id].origin, "car:",
                          self.current_location)
                    print("embark", passenger_id, self.passengers[passenger_id].origin == self.current_location)
                if self.passengers[passenger_id].origin == self.current_location:
                    embarkation_candidates.add(passenger_id)


        to_be_removed = set([])
        # traverse the pairs one-by-one.
        for pair in self.current_partial_order:
            if pair[0] not in embarkation_candidates:
                break
            else:
                if pair[1] == 'o':
                    passenger_id = pair[0]
                    self.passengers[passenger_id].travelling = True
                    self.passengers[passenger_id].start_travelling_time = timer
                    to_be_removed.add(pair)
        for pair in to_be_removed:
            self.current_partial_order.remove(pair)

        if verbose and len(to_be_removed)>0:
            print("\t passengers embarked:")
            print("\t\t ", to_be_removed)
            print("\t\t current partial order", self.current_partial_order)

    def remove_passengers(self, timer: int, verbose=False, debug=False):
        to_be_removed = set()
        for passenger_id in self.passengers:
            if self.passengers[passenger_id].travelling is True:
                if self.passengers[passenger_id].destination == self.current_location:
                    finished_passenger: Rider = self.passengers[passenger_id]
                    finished_passenger.finished = True
                    to_be_removed.add(passenger_id)
                    finished_passenger.ex_post_finishing_time = timer
                    finished_passenger.update_final_utility()

        for passenger_id in to_be_removed:
            if verbose:
                print(
                    f' rider {passenger_id} disembarks car {self.id} in location {self.current_location} at time {timer}')
            self.passengers.pop(passenger_id, None)
            removed = (passenger_id, 'd')
            self.current_partial_order.remove(removed)

            if verbose:
                print('\t removed order part:', removed)
                print('\t current partial order', self.current_partial_order)



    def order_to_locations(self, order: Tuple, new_rider: Rider, from_current_location=True):
        """
        Given an order for the allocated passengers, get a list of locations.

        :param from_current_location: if true then location[0] == current location
        :param order:
        :param new_rider:
        :return: List of locations.
        """
        if from_current_location:
            locations = [self.current_location]
        else:
            locations = []

        for order_pair in order:
            i = int(order_pair[0])
            if i == new_rider.id:
                if order_pair[1] == 'o':
                    locations.append(new_rider.origin)
                if order_pair[1] == 'd':
                    locations.append(new_rider.destination)
            if i in self.passengers and i != new_rider.id:
                if order_pair[1] == 'o':
                    locations.append(self.passengers[i].origin)
                if order_pair[1] == 'd':
                    locations.append(self.passengers[i].destination)
        return locations

    def shortest_path_from_locations(self, locations: List[Tuple], grid: Grid, from_current_location=False):
        if from_current_location:
            temp = [self.current_location] + locations
        else:
            temp = locations

        locations_time = 0
        for i in range(0, len(temp) - 1):
            # print(temp[i], temp[i+1])
            locations_time += grid.shortest_path(temp[i], temp[i + 1])
        return locations_time

    def compute_current_shortest_paths(self, not_yet_travelling_riders: Set[Rider], grid: Grid, debug=False):
        """
            Compute all shortest paths between passengers, car location and the
            new rider(s).

            Two things: 1 - Compute all shortest paths in advance
                        2 - Use the astar
        """

        graph = grid.graph

        if debug:
            print("debugging compute_current_shortest_paths")

        passengers_destinations: dict[int, Tuple] = dict()
        for passenger_id in self.passengers:
            passengers_destinations[passenger_id] = self.passengers[passenger_id].destination

        new_riders_destinations = dict()
        new_riders_origins = dict()

        for rider in not_yet_travelling_riders:
            new_riders_destinations[rider.id] = rider.destination
            new_riders_origins[rider.id] = rider.origin

        if debug:
            print("passenger destinations", passengers_destinations)
            print("not travelling origins", new_riders_origins)
            print("not travelling destinations", new_riders_destinations)

        # car location to  passenger destinations
        for passenger in passengers_destinations:
            if debug:
                print(passenger, passengers_destinations[passenger], 'd')
            self.current_shortest_paths[('c', (passenger, 'd'))] = grid.shortest_path(
                self.current_location, passengers_destinations[passenger])

        # car location to all new riders origins
        for passenger in new_riders_origins:
            if debug:
                print(passenger, new_riders_origins[passenger], 'o')
            self.current_shortest_paths[('c', (passenger, 'o'))] = grid.shortest_path(
                self.current_location, new_riders_origins[passenger])

        # new rider origins to passengers destinations

        for passenger_a in new_riders_origins:
            for passenger_b in passengers_destinations:
                if debug:
                    print("o", passenger_a, new_riders_origins[passenger_a])
                if debug:
                    print("d", passenger_b,
                          passengers_destinations[passenger_b])
                self.current_shortest_paths[((passenger_a, 'o'), (passenger_b, 'd'))] = grid.shortest_path(
                    new_riders_origins[passenger_a], passengers_destinations[passenger_b])

        # new rider origins to new_rider destinations
        for passenger_a in new_riders_origins:
            for passenger_b in new_riders_destinations:
                if debug:
                    print("o:", passenger_a, new_riders_origins[passenger_a])
                if debug:
                    print("d:", passenger_b,
                          new_riders_destinations[passenger_b])
                self.current_shortest_paths[((passenger_a, 'o'), (passenger_b, 'd'))] = grid.shortest_path(
                    new_riders_origins[passenger_a], new_riders_destinations[passenger_b])

        # new rider destination to new_rider origin
        for passenger_a in new_riders_destinations:
            for passenger_b in new_riders_origins:
                if debug:
                    print("d:", passenger_a, new_riders_destinations[passenger_a])
                if debug:
                    print("o:", passenger_b,
                          new_riders_origins[passenger_b])
                self.current_shortest_paths[((passenger_a, 'd'), (passenger_b, 'o'))] = grid.shortest_path(
                    new_riders_destinations[passenger_a], new_riders_origins[passenger_b])

        # new rider destination to new_rider destination
        for passenger_a in new_riders_destinations:
            for passenger_b in new_riders_origins:
                if debug:
                    print("d:", passenger_a, new_riders_destinations[passenger_a])
                if debug:
                    print("o:", passenger_b,
                          new_riders_destinations[passenger_b])
                self.current_shortest_paths[((passenger_a, 'd'), (passenger_b, 'o'))] = grid.shortest_path(
                    new_riders_destinations[passenger_a], new_riders_destinations[passenger_b])

        # new rider origins to new_rider origins
        for passenger_a in new_riders_origins:
            for passenger_b in new_riders_origins:
                if debug:
                    print("o:", passenger_a, new_riders_origins[passenger_a])
                if debug:
                    print("o:", passenger_b,
                          new_riders_origins[passenger_b])
                self.current_shortest_paths[((passenger_a, 'o'), (passenger_b, 'o'))] = grid.shortest_path(
                    new_riders_origins[passenger_a], new_riders_origins[passenger_b])

        # passengers to/from new riders origins/dest and other passengers dest
        for passenger_a in passengers_destinations:
            for passenger_b in new_riders_origins:
                if debug:
                    print("a:", passenger_a,
                          passengers_destinations[passenger_a])
                if debug:
                    print("b:", passenger_b,
                          new_riders_origins[passenger_b])
                self.current_shortest_paths[((passenger_a, 'd'), (passenger_b, 'o'))] = grid.shortest_path(
                    passengers_destinations[passenger_a], new_riders_origins[passenger_b])
                self.current_shortest_paths[((passenger_b, 'o'), (passenger_a, 'd'))] = grid.shortest_path(
                    new_riders_origins[passenger_b], passengers_destinations[passenger_a])

            for passenger_b in new_riders_destinations:
                if debug:
                    print("a:", passenger_a,
                          passengers_destinations[passenger_a])
                if debug:
                    print("b:", passenger_b,
                          new_riders_destinations[passenger_b])
                self.current_shortest_paths[((passenger_a, 'd'), (passenger_b, 'd'))] = grid.shortest_path(
                    passengers_destinations[passenger_a], new_riders_destinations[passenger_b])
                self.current_shortest_paths[((passenger_b, 'd'), (passenger_a, 'd'))] = grid.shortest_path(
                    new_riders_destinations[passenger_b], passengers_destinations[passenger_a])

            for passenger_b in passengers_destinations:
                if passenger_a != passenger_b:
                    if debug:
                        print("a:", passenger_a,
                              passengers_destinations[passenger_a])
                    if debug:
                        print("b:", passenger_b,
                              passengers_destinations[passenger_b])
                    self.current_shortest_paths[((passenger_a, 'd'), (passenger_b, 'd'))] = nx.shortest_path_length(
                        graph, passengers_destinations[passenger_a], passengers_destinations[passenger_b])
                    self.current_shortest_paths[((passenger_b, 'd'), (passenger_a, 'd'))] = nx.shortest_path_length(
                        graph, passengers_destinations[passenger_b], passengers_destinations[passenger_a])

        if debug:
            print("current shortest paths:")
            pprint(self.current_shortest_paths)

    def compute_times(self, order: Order, grid: Grid, new_rider: Rider, debug=False) -> object:
        """
        Given an order, compute the finishing times/embarkation times and
        the times of passenger changes, for the time invoked.
        """

        number_of_passengers = len(self.passengers)
        total_time = 0
        times_of_change = {0: number_of_passengers}
        finishing_times = dict()
        embarkation_times = dict()
        if debug:
            print(order)

        for pair in Util.chain_iterator(order):
            if debug:
                print("\npair", pair)
            if pair in self.current_shortest_paths:
                total_time = total_time + self.current_shortest_paths[pair]
            else:
                if pair[0] == 'c':
                    left = self.current_location
                elif pair[0][0] in self.passengers:
                    if pair[0][1] == 'o':
                        left = self.passengers[pair[0][0]].origin
                    if pair[0][1] == 'd':
                        left = self.passengers[pair[0][0]].destination
                elif pair[0][0] == new_rider.id:
                    if pair[0][1] == 'o':
                        left = new_rider.origin
                    if pair[0][1] == 'd':
                        left = new_rider.destination
                if debug:
                    print("left", left )
                if pair[1][0] in self.passengers:
                    if pair[1][1] == 'o':
                        right = self.passengers[pair[1][0]].origin
                    if pair[1][1] == 'd':
                        right = self.passengers[pair[1][0]].destination
                elif pair[1][0] == new_rider.id:
                    if pair[1][1] == 'o':
                        right = new_rider.origin
                    if pair[1][1] == 'd':
                        right = new_rider.destination
                if debug:
                    print("right", right)
                    print("pair", pair)
                    print("left,right:", left,right)
                length = grid.shortest_path(left, right)
                if pair[0] != 'c':
                    self.current_shortest_paths[pair] = length
                total_time = total_time + length

                if debug:
                    print("shortest path", length)
                    print("total route time", total_time)

            if pair[1][1] == 'd':
                number_of_passengers = number_of_passengers - 1
                times_of_change[total_time] = number_of_passengers
                finishing_rider = pair[1][0]
                finishing_times[finishing_rider] = total_time

            if pair[1][1] == 'o':
                number_of_passengers = number_of_passengers + 1
                times_of_change[total_time] = number_of_passengers
                embarkation_rider = pair[1][0]
                embarkation_times[embarkation_rider] = total_time
        if debug:
            print("shortest paths")
            print(self.current_shortest_paths)

        return finishing_times, embarkation_times, times_of_change, total_time

    def passengers_in_cars(self, order: Tuple[Tuple], debug=False) -> Dict[int, Set]:
        """
        Given an order, find the time intervals shared by riders

        :param grid:
        :param order:
        :return:
        """

        if debug:
            print("\t testing")
            print("passengers allocated", self.passengers.keys())
        # print(set(self.passengers.keys()))

        if debug:
            print("travelling passengers", [id for id in self.passengers if self.passengers[id].travelling == True])

        stack = set([id for id in self.passengers if self.passengers[id].travelling == True])
        time_intervals = dict()
        time_intervals[0] = copy.deepcopy(stack)
        if debug:
            print(stack)
        k = 1
        for part in order:
            if part[1] == 'o':
                stack.add(part[0])
            if part[1] == 'd':
                stack.remove(part[0])
            time_intervals[k] = copy.deepcopy(stack)
            k = k + 1

        return time_intervals

    def is_capacity_constraint_satisfied(self, order: Tuple, riders: List[Rider], debug=False):
        """
        Given an order, and a new rider, check if more than self.capacity passingers
        are travelling at any time
        :param order:
        :return:
        """

        if len(self.passengers) + len(riders) <= self.capacity:
            return True
        else:
            number_of_passengers = len(
                [rider for rider in self.passengers if self.passengers[rider].travelling is True])
            for pair in Util.chain_iterator(order):
                if pair[1][1] == 'd':
                    number_of_passengers = number_of_passengers - 1
                if pair[1][1] == 'o':
                    number_of_passengers = number_of_passengers + 1
                    if number_of_passengers > self.capacity:
                        return False
            return True

    def propose_route_simple(self, new_rider: Rider, grid: Grid, debug=False):
        """
        The car proposes the cost of least travelling time
        at a fixed price, equal to the cost value
        """

        not_yet_travelling_passengers_ids = set(
            [rider_id for rider_id in self.passengers if self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers_ids.add(new_rider.id)

        not_yet_travelling_passengers = set([self.passengers[rider_id] for rider_id in self.passengers if
                                             self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers.add(new_rider)

        self.compute_current_shortest_paths(not_yet_travelling_passengers, grid, debug=False)
        if debug:
            print("shortest paths:")
            pprint(self.current_shortest_paths)

        passengers_ids = {passenger for passenger in self.passengers}
        order_generator = Order(self.passengers)

        if debug:
            print("not yet travelling:", not_yet_travelling_passengers_ids)

        to_append_list = []
        if debug:
            print("passenger ids:", passengers_ids)
        for order in order_generator.all_restricted_orders(not_yet_travelling_passengers_ids):
            # check if the number of passenger exceeds the cars capacity in the route
            if self.is_capacity_constraint_satisfied(order, [new_rider]):
                if debug:
                    print("order: ", order)
                    print("locations:", self.order_to_locations(order, new_rider))
                finishing_times, embarkation_times, times_of_change, total_route_time = self.compute_times(
                    order)
                if debug:
                    print("finishing times", finishing_times)
                    print("embarkation times", embarkation_times)
                    print("times of change", times_of_change)
                    print("total route time", total_route_time)
                to_append = {'order': order,
                             'location_order': self.order_to_locations(order, new_rider),
                             'finishing_time': finishing_times[new_rider.id],
                             'payment': self.cost * total_route_time,
                             'car_id': self.id,
                             'total_route_time': total_route_time}
                #            values[order] = {'time': total_route_time, 'price': self.cost * total_route_time }
                #            print(values)
                to_append_list.append(to_append)

            dummy_proposal = {
                'total_route_time': 100000000,
            }
            to_append_list.append(dummy_proposal)
            values = pd.DataFrame.from_records(to_append_list)

        # find the route of minimum cost and propos
        quickest_route_loc = values["total_route_time"].idxmin()
        return values.loc[quickest_route_loc]

    def propose_route_with_externalities(self, new_rider: Rider, grid: Grid, timer: int, debug=False, verbose=False, silent=False) -> Tuple:

        """
        The car proposes the trip maximum social welfare, for the new rider.
        The new rider is charged the externality it causes to the other riders.
        """

        if verbose:
            print()
            if self.id > 0:
                print("proposal by car", self.id)
            else:
                print("proposal by new car")
            print("current car location", self.current_location)

        not_yet_travelling_passengers_ids = set(
            [rider_id for rider_id in self.passengers if self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers_ids.add(new_rider.id)

        not_yet_travelling_passengers = set([self.passengers[rider_id] for rider_id in self.passengers if
                                             self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers.add(new_rider)

        if debug:
            print("passenger", self.passengers.keys(), "\n \t not yet travelling passengers",
              not_yet_travelling_passengers_ids)

        if verbose:
            print("current order", self.current_order)
            print("current order locations", self.order_to_locations(self.current_order, new_rider))
            print("current partial order", self.current_partial_order)

        finishing_times_old, _, _, total_route_time_old = self.compute_times(self.current_partial_order, grid, new_rider)

        if verbose:
            print("current finishing times (marginal):", finishing_times_old)

        if debug:
            print("finishing times old:", finishing_times_old)

        passengers_ids = {passenger for passenger in self.passengers}
        cleared_order = []
        fixed_order_generator = FixedOrderGenerator(self.current_partial_order)

        if debug:
            print("not yet travelling:", not_yet_travelling_passengers_ids)

        to_append_list = []
        if debug:
            print("passenger ids:", passengers_ids)

        count_orders = 0
        temporary_best_time = np.Inf
        for order in fixed_order_generator.all_fixed_orders(new_rider.id):
            count_orders += 1
            if verbose:
                print(" ")
                print("new order", order, "no:", count_orders)
                print("new order locations", self.order_to_locations(order, new_rider))
            if self.is_capacity_constraint_satisfied(order, [new_rider]):
                if debug:
                    print("order: ", order)
                    print("locations:", self.order_to_locations(order, new_rider))
                finishing_times, _, _, total_route_time = self.compute_times(order, grid, new_rider)

                if verbose:
                    print("new finishing times (marginal):", finishing_times)

                # The new rider pays: a) The part of the ride for which is alone in the car
                #                     b) Compensations for the previous riders

                histogram = self.passengers_in_cars(order, debug=False)
                if verbose:
                    print("\thistogram", histogram)

                    from_current_position_flag = True

                # compensation computation
                compensations = dict([])
                for i in self.passengers:
                    riders_i_payment = self.passengers[i].proposed_payment
                    riders_i_finishing_time = finishing_times[i]+timer
                    riders_i_new_utility = self.passengers[i].utility(riders_i_finishing_time, riders_i_payment)
                    compensations[i] = max(0, self.passengers[i].proposed_utility - riders_i_new_utility)

                if verbose:
                    print("compensations", compensations)
                    print("total_route_time", total_route_time)
                    print("total_route_time_old", total_route_time_old)

                riders_paying_time_new = max(total_route_time-total_route_time_old, 0)
                projected_payment = self.cost * riders_paying_time_new + sum(compensations.values())

                if verbose:
                    print("projected payments:")
                    print("\t\t current way:", projected_payment)
                    print('\t\t utility', new_rider.utility(finishing_times[new_rider.id] + timer, projected_payment))
                    print("riders paying time", riders_paying_time_new)

                if debug:
                    print("finishing times", finishing_times)
                    # print("embarkation times", embarkation_times)
                    # print("times of change", times_of_change)
                    print("total route time", total_route_time)
                to_append = {'order': order,
                             'location order': self.order_to_locations(order, new_rider),
                             'finishing time': finishing_times[new_rider.id]+timer,
                             'total travelling time': finishing_times[new_rider.id],
                             'payment': projected_payment,
                             'car_id': self.id,
                             'total_route_time': total_route_time,
                             'compensations': compensations,
                             'utility': new_rider.utility(finishing_times[new_rider.id]+timer, projected_payment),
                             'histogram': histogram,
                             'riders paying time (new)': riders_paying_time_new,
                             'no of allocated riders': len(self.passengers),
                             'finishing times': finishing_times,
                             }
                to_append_list.append(to_append)
            else:
                if verbose:
                    print(order)
                    print("capacity limit is not satisfied!")

        # If no feasible route exists for the new rider:
        if len(to_append_list) == 0:
            return (1,"No feasible route exists")

        values = pd.DataFrame.from_records(to_append_list)
        if verbose:
            print(values)
        quickest_route_loc = values["utility"].idxmax()
        return (0,values.loc[quickest_route_loc])

    def propose_route_fixed_discount(self, new_rider: Rider, grid: Grid, timer: int, debug=False, verbose=False) -> Tuple:

        """
        The rider pays a fixed discount for using a car with other riders on.
        """

        if len(self.passengers) == 0:
            discount =0
        elif len(self.passengers) == 1:
            discount = 0.1
        else:
            discount = 0.2

        if verbose:
            print()
            if self.id > 0:
                print("proposal by car", self.id)
            else:
                print("proposal by new car")
            print("current car location", self.current_location)

        not_yet_travelling_passengers_ids = set(
            [rider_id for rider_id in self.passengers if self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers_ids.add(new_rider.id)

        not_yet_travelling_passengers = set([self.passengers[rider_id] for rider_id in self.passengers if
                                             self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers.add(new_rider)

        if debug:
            print("passenger", self.passengers.keys(), "\n \t not yet travelling passengers",
              not_yet_travelling_passengers_ids)

        if verbose:
            print("current order", self.current_order)
            print("current order locations", self.order_to_locations(self.current_order, new_rider))
            print("current partial order", self.current_partial_order)

        finishing_times_old, _, _, total_route_time_old = self.compute_times(self.current_partial_order, grid, new_rider)

        if verbose:
            print("current finishing times (marginal):", finishing_times_old)

        if debug:
            print("finishing times old:", finishing_times_old)

        passengers_ids = {passenger for passenger in self.passengers}
        cleared_order = []
        fixed_order_generator = FixedOrderGenerator(self.current_partial_order)

        if debug:
            print("not yet travelling:", not_yet_travelling_passengers_ids)

        to_append_list = []
        if debug:
            print("passenger ids:", passengers_ids)

        count_orders = 0
        temporary_total_time = np.Inf
        for order in fixed_order_generator.all_fixed_orders(new_rider.id):
            count_orders += 1
            if verbose:
                print(" ")
                print("new order", order, "no:", count_orders)
                print("new order locations", self.order_to_locations(order, new_rider))
            if self.is_capacity_constraint_satisfied(order, [new_rider]):
                if debug:
                    print("order: ", order)
                    print("locations:", self.order_to_locations(order, new_rider))
                finishing_times, _, _, total_route_time = self.compute_times(order, grid, new_rider)

                if verbose:
                    print("new finishing times (marginal):", finishing_times)

                histogram = self.passengers_in_cars(order, debug=False)
                if verbose:
                    print("\thistogram", histogram)

                    from_current_position_flag = True
                compensations = dict([])

                if verbose:
                    print("compensations", compensations)

                    print("total_route_time", total_route_time)
                    print("total_route_time_old", total_route_time_old)

                riders_paying_time_new = finishing_times[new_rider.id]
                projected_payment = self.cost * riders_paying_time_new*(1-discount)

                if verbose:
                    print("projected payments:")
                    print("\t\t current way:", projected_payment)
                    print('\t\tutility', new_rider.utility(finishing_times[new_rider.id] + timer, projected_payment))
                    print("riders paying time", riders_paying_time_new)


                if debug:
                    print("finishing times", finishing_times)
                    print("total route time", total_route_time)
                to_append = {'order': order,
                             'location order': self.order_to_locations(order, new_rider),
                             'finishing time': finishing_times[new_rider.id]+timer,
                             'total travelling time': finishing_times[new_rider.id],
                             'payment': projected_payment,
                             'car_id': self.id,
                             'total_route_time': total_route_time,
                             'compensations': compensations,
                             'utility': new_rider.utility(finishing_times[new_rider.id]+timer, projected_payment),
                             'histogram': histogram,
                             'riders paying time (new)': riders_paying_time_new,
                             'no of allocated riders': len(self.passengers),
                             'finishing times': finishing_times,
                             }
                to_append_list.append(to_append)
            else:
                if verbose:
                    print(order)
                    print("capacity limit is not satisfied!")

        if len(to_append_list) == 0:
            return (1,"No feasible route exists")

        values = pd.DataFrame.from_records(to_append_list)
        if verbose:
            print(values)
        quickest_route_loc = values["total_route_time"].idxmin()
        return (0, values.loc[quickest_route_loc])


    def propose_route_fifo(self, new_rider: Rider, grid: Grid, timer: int, debug=False, verbose=False) -> Tuple:

        """
        The rider pays a fixed discount for using a car with other riders on.
        """

        if verbose:
            print()
            if self.id > 0:
                print("proposal by car", self.id)
            else:
                print("proposal by new car")
            print("current car location", self.current_location)

        not_yet_travelling_passengers_ids = set(
            [rider_id for rider_id in self.passengers if self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers_ids.add(new_rider.id)

        not_yet_travelling_passengers = set([self.passengers[rider_id] for rider_id in self.passengers if
                                             self.passengers[rider_id].travelling is False])
        not_yet_travelling_passengers.add(new_rider)

        if debug:
            print("passenger", self.passengers.keys(), "\n \t not yet travelling passengers",
              not_yet_travelling_passengers_ids)

        if verbose:
            print("current order", self.current_order)
            print("current order locations", self.order_to_locations(self.current_order, new_rider))
            print("current partial order", self.current_partial_order)

        finishing_times_old, _, _, total_route_time_old = self.compute_times(self.current_partial_order, grid, new_rider)

        if verbose:
            print("current finishing times (marginal):", finishing_times_old)

        if debug:
            print("finishing times old:", finishing_times_old)

        passengers_ids = {passenger for passenger in self.passengers}
        cleared_order = []

        if debug:
            print("not yet travelling:", not_yet_travelling_passengers_ids)

        to_append_list = []
        if debug:
            print("passenger ids:", passengers_ids)

        order = self.current_partial_order + [(new_rider.id, 'o'), (new_rider.id, 'd')]
        finishing_times, _, _, total_route_time = self.compute_times(order, grid, new_rider)
        riders_paying_time_new = finishing_times[new_rider.id]
        projected_payment = self.cost * riders_paying_time_new
        compensations = dict([]) # only ofr comatibility
        histogram = dict([])

        to_append = {'order': order,
                     'location order': self.order_to_locations(order, new_rider),
                     'finishing time': finishing_times[new_rider.id] + timer,
                     'total travelling time': finishing_times[new_rider.id],
                     'payment': projected_payment,
                     'car_id': self.id,
                     'total_route_time': total_route_time,
                     'compensations': compensations,
                     'utility': new_rider.utility(finishing_times[new_rider.id] + timer, projected_payment),
                     'histogram': histogram,
                     'riders paying time (new)': riders_paying_time_new,
                     'no of allocated riders': len(self.passengers),
                     'finishing times': finishing_times,
                     }

        to_append_list.append(to_append)
        if len(to_append_list) == 0:
            return 1, "No feasible route exists"

        values = pd.DataFrame.from_records(to_append_list)
        if verbose:
            print(values)
        quickest_route_loc = values["total_route_time"].idxmin()
        return 0, values.loc[quickest_route_loc]