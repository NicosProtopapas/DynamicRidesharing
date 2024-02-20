from typing import Dict, Set, Tuple, List
from itertools import permutations
from src.Rider import Rider

DESTINATION = 'd'
ORIGIN = 'o'


class FixedOrderGenerator():
    """

    """

    def __init__(self, current_order: Tuple[Tuple]) -> None:
        super(FixedOrderGenerator, self).__init__()
        self.current_order: Tuple[Tuple] = current_order

    def fifo_order(self, new_rider_id: int):
        origin = (new_rider_id, 'o')
        destination = (new_rider_id, 'd')



    def all_fixed_orders(self, new_rider_id: int):
        origin = (new_rider_id, 'o')
        destination = (new_rider_id, 'd')
        length = len(self.current_order)

        orders = []
        for i in range(0, length+1):
            for j in range(i, length + 2):
                if i != j:
                    temp = dict([])
                    # print(i, j,"\n")
                    temp[i] = origin
                    temp[j] = destination
                    index = 0
                    for k in range(0, length + 2):
                        if k not in temp:
                            temp[k] = self.current_order[index]
                            index += 1

                    new_order = []

                    for k in sorted(temp):
                        new_order.append(temp[k])
                        #print(temp[k],)

                    new_order = tuple(new_order)
                    yield new_order


class Order(object):
    """
    Order: given a list of riders' ids, return all possible orders
    order is a tuple of tuples (i,'o') for the origin of and
    (i,'d') for destination of rider i.

    Restricted order: a set of riders is in the car, hence only destination
    location matters.
    """

    def __init__(self, riders: Dict, initialize=True):
        super(Order, self).__init__()
        self.riders = riders  # this should be dict
        self.orders = set([])
        self.restricted_orders = set([])
        if initialize:
            self.all_orders()

    def is_valid_order(self, order: Tuple[Tuple]):
        """
            check if a (general) order is valid;
            This can put in a preprocessing case--> create a table
        """

        visited_origin = set([])
        for o in order:
            if o[1] == 'o':
                visited_origin.add(o[0])
            if o[1] == 'd' and o[0] not in visited_origin:
                return False
        return True

    def is_valid_restricted_order(self, order, new_riders, debug=False):
        """
            check if a (restricted) order is valid;
            This can put in a preprocessing case--> create a table
        """

        if debug:
            print(new_riders.keys())

        visited_origin = set([])
        for o in order:
            if o[1] == 'o' and o[0] in new_riders:
                visited_origin.add(o[0])
                if debug:
                    print("visited origin:", visited_origin)
            if o[1] == 'd' and o[0] not in visited_origin:
                if debug:
                    print(o[0], o[0] in new_riders)
                if o[0] in new_riders:
                    if debug:
                        print("order rejected")
                    return False
        if debug:
            print("return True")
        return True

    def all_orders(self, debug=False):
        origins = [(i, 'o') for i in self.riders]
        destinations = [(i, 'd') for i in self.riders]

        if debug:
            print("origins:", origins)
            print("destinations", destinations)

        for order in permutations(origins + destinations):
            if self.is_valid_order(order):
                self.orders.add(order)

    def all_restricted_orders(self, not_yet_in_car_riders: Set, debug=False):
        origins = [(i, 'o') for i in not_yet_in_car_riders]
        destinations = [(i, 'd') for i in not_yet_in_car_riders.union(self.riders)]

        if debug:
            print("origins:", origins)
            print("destinations", destinations)

        for order in permutations(origins + destinations):
            if self.is_valid_restricted_order(order, not_yet_in_car_riders, debug):
                if debug:
                    print("order accepted")
                yield (order)
                # self.restricted_orders.add(order)
