from dataclasses import dataclass, field
from collections import deque
from typing import Tuple, List, Dict
from src.Grid import Grid
from src.Utilities import all_equal


@dataclass(eq=True)
class Rider:
    """
        Class to create riders.
        Origin and destination are given as tuple of coordinates.
    """
    id: int
    origin: Tuple
    destination: Tuple
    starting_time: int
    value_of_time: float
    optimal_travelling_time: int = None
    # true if the rider is allocated in a car, but has not yet been in the car
    allocated: bool = False
    travelling: bool = False
    finished: bool = False
    allocated_car: int = None  # selected car. At first is None
    start_travelling_time: int = None
    proposed_payment: float = None
    proposed_travelling_time: int = None
    proposed_finishing_time: int = None
    ex_post_finishing_time: int = None  # ex-post fin
    ex_post_travelling_time: int = 0
    ex_post_total_time: int = 0
    ex_post_utility: float = None
    compensations_in: Dict[int, float] = field(default_factory=lambda: dict([]))
    compensations_out: Dict[int, float] = field(default_factory=lambda: dict([]))
    proposed_utility: float = None
    optimal_payment: float = None
    proposed_route: List[Tuple] = None
    proposed_order: Tuple[Tuple] = None
    direct_route_time: int = None
    current_location: int = None
    location_history: Dict[int, float] = field(default_factory=lambda: dict([]))
    last_ten: deque = field(default_factory=lambda: deque([], maxlen=10))

    def print_quick_details(self):
        print(
            f'Rider {self.id} appears at time {self.starting_time} to travel from location {self.origin} to location {self.destination}')
        print(f'Rider {self.id}  loses {self.value_of_time} of utility for each time-step divereted from the optimal route')

    def print_time_metrics(self):
        print("")
        print("rider", self.id, " timing metrics:\n")
        print("\t starting time:", self.starting_time)
        print("\t ex-post finishing time:", self.ex_post_finishing_time)
        print("\t ex-post travelling time:", self.ex_post_travelling_time)
        print("\t ex-post waiting time:", self.ex_post_total_time - self.ex_post_travelling_time)
        print("\t ex-post total time:", self.ex_post_total_time)
        print("\t optimal time:", self.optimal_travelling_time)

    def print_metrics(self):
        print("")
        print("rider", self.id, " final info and metrics:\n")
        print("origin:", self.origin)
        print("destination:", self.destination)
        print("value of time:", self.value_of_time)
        print("allocated car:", self.allocated_car)
        print("\t starting time:", self.starting_time)
        print("\t proposed finishing time:", self.proposed_finishing_time)
        print("\t ex-post finishing time:", self.ex_post_finishing_time)
        print("\t ex-post travelling time:", self.ex_post_travelling_time)
        print("\t ex-post waiting time:", self.ex_post_total_time - self.ex_post_travelling_time)
        print("\t ex-post total time:", self.ex_post_total_time)
        print("\t optimal time:", self.optimal_travelling_time)
        print("\t direct time:", self.direct_route_time)
        print("\t proposed payment:", self.proposed_payment)
        print("\t optimal payment:", self.optimal_payment)
        print("\t proposed utility:", self.proposed_utility)
        print("\t ex-post utility:", self.ex_post_utility)
        print("\t proposed route:", self.proposed_route)
        print("\t proposed order:", self.proposed_order)
        print("\t compensations out:", self.compensations_out)
        print("\t compensations in:", self.compensations_in)
        print("\t compensations in total:", sum(self.compensations_in.values()))


    def init(self):
        self.current_location = self.origin

    def trace_locations(self, location, timer):
        if self.travelling and not self.finished:
            self.current_location = location
            self.last_ten.append(location)
            #self.location_history[timer]= location

    def check_if_stopped(self, location):
        if all_equal(self.last_ten) and len(self.last_ten)> 2:
            print(self.last_ten)
            print(f"rider {self.id} remains in the same place ")
            return -1


    def set_optimal_travelling_time(self, grid: Grid, depot_locations: List[Tuple], active_car_locations: List[Tuple]):
        times = set([])
        direct_route = grid.shortest_path(self.origin, self.destination)
        self.direct_route_time = direct_route
        for depot_location in depot_locations:
            times.add(
                grid.shortest_path(depot_location, self.origin) + direct_route
            )
        for car_location in active_car_locations:
            times.add(
                grid.shortest_path(car_location, self.origin) + direct_route
            )
        #print("times", times, "min.", min(times))
        self.optimal_travelling_time = min(times)

    def utility(self, finishing_time: int, payment: float):
        """
        :param payment: the total payment proposed by the car
        :type finishing_time: finishing time proposed
        """
        self.optimal_payment = self.value_of_time * self.optimal_travelling_time
        return -self.value_of_time * ((finishing_time - self.starting_time) - self.optimal_travelling_time) - payment

    def __hash__(self):
        return hash(self.id)

    def update_metrics(self):
        if self.allocated and not self.finished:
            self.ex_post_total_time += 1
        if self.travelling and not self.finished:
            self.ex_post_travelling_time += 1

    def update_final_utility(self, silent=True):
        self.ex_post_utility = self.utility(self.ex_post_finishing_time, self.proposed_payment) + sum(
            self.compensations_in.values())
        if not silent:
            print("utility part", self.utility(self.ex_post_finishing_time, self.proposed_payment))
            print("total compensations in", sum(self.compensations_in.values()))
            print("utility full", self.utility(self.ex_post_finishing_time, self.proposed_payment) + sum(self.compensations_in.values()))
            print("utility full -- saved", self.ex_post_utility)

    def allocate_rider(self, allocated_car_id: int, proposed_finishing_time: int, proposed_payment: float,
                       compensations: Dict[int, float], route_order: Tuple[Tuple], route: List[Tuple]):
        """

        :type compensations: object
        """

        self.proposed_payment = proposed_payment
        self.proposed_finishing_time = proposed_finishing_time
        self.allocated_car = allocated_car_id
        self.compensations_out = compensations
        self.proposed_utility = self.utility(proposed_finishing_time, proposed_payment)
        self.proposed_route = route
        self.proposed_order = route_order
