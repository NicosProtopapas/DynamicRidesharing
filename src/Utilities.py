from typing import Dict, Tuple, List
from numpy import abs
from itertools import groupby

"""
    A list of utility functions
"""


def all_equal(iterable):
    g = groupby(iterable)
    return next(g, True) and not next(g, False)

def are_dictionary_keys_unique(a: Dict, b: Dict):
    for key in a:
        if key in b:
            return False
    return True


def merge_dicts_if_unique(a: Dict, b: Dict):
    if are_dictionary_keys_unique(a, b):
        # dictionary unpacking
        return {**a, **b}

def dist(x,y):
  s=0
  for i in range(0, len(x)):
    s= s+ abs(x[i]-y[i])
  return s

def dist_s(a):
  s=0
  for i in range(0,len(a)-1):
    #print(a[i],a[i+1])
    #print(dist(a[i],a[i+1]))
    s+=dist(a[i],a[i+1])
  return(s)

def finishing_times(order, locations):
    if len(order) != len(locations)-1:
        return "Error!"
    print(order)
    current_location=locations[0]
    for i in range(1,len(order)):
        print(order[i], locations[i])




def chain_iterator(order: Tuple):
    iter_obj = iter(order)

    element = 'c'
    while True:
        try:
            previous_element = element
            element = next(iter_obj)
            yield previous_element, element
        except StopIteration:
            break


def combine_path(paths: List):
    if not paths:
        path = []
    else:
        path = paths[0]
        paths.pop(0)
        for path_part in paths:
            print("pp", path_part)
            print("path", path)
            if path_part[0] == path[-1]:
                path = path[0:-1] + path_part
            else:
                return "Error"
    return path


def dist(source: Tuple, destination: Tuple):
    """
    The l1  distance between two nodes on the plane
    @param source: Tuple
    @param destination:
    @return:
    """
    """
    @param source: 
    @param destination: 
    @param p: 
    @return: 
    """

    (x1, y1) = source
    (x2, y2) = destination

    return abs(x1 - x2) + abs(y1 - y2)
