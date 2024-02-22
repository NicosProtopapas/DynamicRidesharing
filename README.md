# DynamicRidesharing
This is a repository for the code of the paper "Online Decentralised Mechanisms for Dynamic Ridesharing", which will appear in AAMAS 2024. 

A link to the paper will be added soon.

## Instructions
Instructions are provide for any Linux distribution. Windows users can WSL
(see: https://docs.microsoft.com/en-us/windows/wsl/install-win10)

### Requirements
    - python3.10 or newer
    - python3.10-venv

### How to use

    - make sure the packages in requirements are installed in your distribution and run.sh has permission to run.
    - Use config.yml to pass parameters to the simulator. then use run.sh
 
If you prefer to run the simulation manually for any reason, follow the general instructions below:

   1) Ensure python3.10 is installed in your system
   2) Create a virtual environment and manually install the packages from requirments.txt
   -- conda users: the proverty package need to be installed with pip
   3) run the ./run.sh file. Make sure it has permission to run


### Filling config.yml

The config.yml file initializes our experiments. The following is an example with comments on how to use it.

  'name': Test1

   Gives the name of the experiment. Every experiments uses a different name.

  'numbers_of_riders': [10,20,30]

   A list determining the number of riders for which to run the experiments

  'iterations': 3

  How many times the simulation will run, for each number of riders

  'grid_x': 50
  'grid_y': 50

   Grid size

  'seed': 545

  'uniform_low': 0
  'uniform_high': 10

  the bounds of the uniform distribution for the value of time

  'cost_flag': "Random"

  Possible values: "Fixed" or 'Random'. Determines whether the cost is fixed or uses a uniform distribution.

  'cost': [10,30]

  For fixed cost, give a single real number. For For "random" give upper and lower bounds for a uniform distribution.

  'capacity_flag': "Random"

  Possible values: "Fixed" or 'Random'. Determines whether the capacity is fixed or uses a given distribution.

  'capacity':
    'pool':  [4,6,8,10]
    'probabilities': [0.5,0.1,0.3,0.1]

    pool is a list of integers. Probabilities is a list of real number. Probabilities should sum to 1, and both list should
    have the same size.

    In this example, a car of capacity 4 appers with probability 0.5


  'lambda': 5

    The parameter for the Poisson distribution.

  'number_of_depots': 3

   The maximum number of depots.

  'maximum_number_of_cars': 10

  The maximum number of cars.
