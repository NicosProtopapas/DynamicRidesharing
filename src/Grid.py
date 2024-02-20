from typing import List, Tuple, Dict
import networkx as nx
from itertools import permutations
import pandas as pd

def dist(source: Tuple , destination: Tuple):
    """
    The l1  distance between two nodes on the plane
    @param source: Tuple
    @param destination:
    @param p: 1 or 2
    @return:
    """
    (x1, y1) = source
    (x2, y2) = destination

    return abs(x1 - x2) + abs(y1 - y2)

"""
An undelying undirected, grid graph for the experaments.
"""


class Grid:
    """
        docstring for Grid. The grid uses networkx
        each location is tuple in (0,0) to (length-1,width-1).
        Each edge needs one unit of time to be traversed.
    """

    def __init__(self, length: int, width: int) -> object:
        """

        @rtype: object
        """
        self.length = length
        self.width = width
        self.graph = nx.grid_2d_graph(length, width)

    def get_size(self):
        return self.length, self.width

    def check_route(self, route: List):
        """
            Given a list of nodes in the graph, find if it is a valid path
        """
        return nx.is_path(self.graph, route)

    def is_valid_order(self, order):
        """
            check if an order is valid;
            This can put in a preprocessing case--> create a table
        """

        visited_origin = set([])
        for o in order:
            if o[1] == 'o':
                visited_origin.add(o[0])
            if o[1] == 'd' and o[0] not in visited_origin:
                return False
        return True

    def order_to_location_dict(self, order, riders):
        """
        transform an order of riders to a location list.
        """
        i = 1
        location = dict()
        for o in order:
            if o[1] == 'd':
                location[i] = riders[o[0]].destination
            if o[1] == 'o':
                location[i] = riders[o[0]].origin
            i = i+1
        return location

    def shortest_path(self, start: Tuple, finish: Tuple, method='astar', include_path=False):
        """
        get the shortest path of the grid
        """
        if method == 'dijkstra':
            length = nx.shortest_path_length(self.graph, start, finish)
            if include_path:
                path = nx.shortest_path(self.graph, start, finish)
                return (length, path)
            return length

        if method == 'astar':
            path = nx.astar_path(self.graph, start, finish, heuristic = dist )
            length = len(path) -1
            if include_path:
                return (length, path)
            return(length)

    def riders_finishing_time(self, order, car_location: Tuple, rider_id: int, riders: Dict, check_order_validity=False):
        # given an order and a rider, find finishing time
        if check_order_validity:
            pass
            # write the code
        #locations = self.order_to_location_dict(order, riders)
        #locations[0] = car_location

    def shortest_paths(self, car_location: Tuple, riders: Dict):
        """
            find all shortest paths betweeen riders origin and dest, and the car
        """

        self.shortest_paths_dict = dict()
        for i in riders:
            for j in riders:
                self.shortest_paths_dict[((i, 'o'), (j, 'o'))] = nx.shortest_path_length(
                    self.graph, riders[i].origin, riders[j].origin)
                self.shortest_paths_dict[((i, 'o'), (j, 'd'))] = nx.shortest_path_length(
                    self.graph, riders[i].origin, riders[j].destination)
                self.shortest_paths_dict[((i, 'd'), (j, 'o'))] = nx.shortest_path_length(
                    self.graph, riders[i].destination, riders[j].origin)
                self.shortest_paths_dict[((i, 'd'), (j, 'd'))] = nx.shortest_path_length(
                    self.graph, riders[i].destination, riders[j].destination)

        for i in riders:
            self.shortest_paths_dict[('c', (i, 'o'))] = nx.shortest_path_length(
                self.graph, riders[i].origin, riders[j].origin)
            self.shortest_paths_dict[('c', (i, 'd'))] = nx.shortest_path_length(
                self.graph, riders[i].origin, riders[j].destination)

    def order_to_route(self, car_id, order):
        l = len(order)
        for i in range(0, l+1):
            pass

    def all_shortest_paths_file(self, filename):
        """
        Create a dict with all shortest paths, for all
        """

        shortest_paths = dict([])
        for i in self.graph.nodes():
            for j in self.graph.nodes():
                if i != j:
                    length, path = self.shortest_path(i, j, True)
                    shortest_paths[(i, j)] = {"TIME": length, "PATH": path}

        #pprint(shortest_paths)
        #dtypes = {"TIME": 'int', "PATH": 'varchar255'}
        df = pd.DataFrame(data=shortest_paths).T
        filename = filename + "2.db"
        print(df.dtypes)
        print(df)
        df.to_sql(filename, con=engine, index_label='ID')
        #df.to_pickle(filename)

    def routes_computation(self, car_location: Tuple, riders: Dict, debug=False):
        """
        Given a set of start-end pairs, compute the shortest path starting
        from car_location and visit all destinations, checking all valid
        orderings of arrivals: order according to the riders key.
        """

        n = len(riders)
        # create the sets to create all possible orderings
        origins = [(i, 'o') for i in riders]
        destinations = [(i, 'd') for i in riders]
        counter = 0

        if debug:
            print("origins:", origins)
            print("destinations", destinations)

        for order in permutations(origins+destinations):
            counter += 1
            if self.is_valid_order(order):
                pass

    def routes(self, car_location: Tuple, riders: Dict):
        """
        Given a set of start-end pairs, compute the shortest path starting
        from car_location and visit all destinations, checking all valid
        orderings of arrivals: order according to the riders key.
        """

        n = len(riders)
        origins = [(i, 'o') for i in range(0, n)]
        destinations = [(i, 'd') for i in range(0, n)]
        routes = dict([])
        routes_length = dict([])
        orders = dict([])
        counter = -1
        for order in permutations(origins+destinations):
            counter += 1
            #print(counter)
            if self.is_valid_order(order):
                locations = self.order_to_location_dict(order, riders)
                locations[0] = car_location
                for l in locations:
                    if l < len(locations)-1:
                        1
                        if counter not in routes:
                            routes[counter] = []
                        if counter not in routes_length:
                            routes_length[counter] = 0

                            routes[counter] = routes[counter] + nx.shortest_path(self.graph,
                                                                                 locations[l], locations[l+1])
                            routes_length[counter] = routes_length[counter] + nx.shortest_path_length(self.graph,
                                                                                                      locations[l], locations[l+1])
            orders[counter] = order
        return routes, routes_length, orders
