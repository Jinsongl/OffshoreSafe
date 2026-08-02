"""Run the optional UQpy compatibility benchmark."""

from __future__ import annotations

import numpy as np
from uqra import RandomVariable, RandomVector, ReliabilityProblem, get_backend

variables = RandomVector(
    [
        RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
        RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
    ]
)
problem = ReliabilityProblem(variables, lambda x: x[0] - x[1])
native = problem.solve("FORM", backend="native")
external = problem.solve("FORM", backend="uqpy")
assert abs(external.beta - 40.0 / np.sqrt(200.0)) <= 4.0e-3
assert abs(external.beta - native.beta) <= 4.0e-3

correlated = RandomVector(
    variables.variables,
    correlation_matrix=[[1.0, 0.4], [0.4, 1.0]],
)
correlated_form = ReliabilityProblem(correlated, lambda x: x[0] - x[1]).solve(
    "FORM", backend="uqpy"
)
assert abs(correlated_form.beta - 40.0 / np.sqrt(120.0)) <= 8.0e-3

sorm = problem.solve("SORM", backend="uqpy")
assert np.isclose(sorm.pf, external.pf, rtol=2.0e-3)

sampler = get_backend("uqpy")
lhs = sampler.sample("LHS", 3, 32, random_state=42)  # type: ignore[attr-defined]
bins = np.floor(lhs.samples * 32).astype(int)
assert all(np.unique(bins[:, column]).size == 32 for column in range(3))
print(
    {
        "uqpy_version": external.metadata["backend_version"],
        "rs_form_beta": external.beta,
        "correlated_form_beta": correlated_form.beta,
        "lhs_shape": lhs.samples.shape,
    }
)
