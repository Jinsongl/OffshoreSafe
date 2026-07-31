"""Use the Milestone 0.2 distributions and random-vector model."""

import numpy as np
from uqra import Normal, RandomVariable, RandomVector

strength = RandomVariable("strength", "Normal", {"mean": 350.0, "std": 20.0})
load = RandomVariable("load", "Normal", {"mean": 250.0, "std": 30.0})
joint = RandomVector(
    [strength, load],
    correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
)

strength_distribution = Normal(**strength.parameters)
print(strength_distribution.cdf(350.0))
print(joint.names)
