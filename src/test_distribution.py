import numpy as np
elements = [3, 4, 8, 10]
probabilities = [0.2, 0.5, 0.1, 0.2]

print(np.random.choice(elements, 100, p=probabilities))


