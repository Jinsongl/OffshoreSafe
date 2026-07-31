"""Run the optional OpenTURNS reliability compatibility benchmark."""

from __future__ import annotations

import numpy as np
from uqra import (
    SORM,
    LimitStateFunction,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
)

variables = RandomVector(
    [
        RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
        RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
    ]
)
problem = ReliabilityProblem(variables, lambda x: x[0] - x[1])
native = problem.solve("FORM", backend="native")
external = problem.solve("FORM", backend="openturns")
assert abs(external.beta - 40.0 / np.sqrt(200.0)) <= 2.0e-4
assert abs(external.beta - native.beta) <= 2.0e-4

for correction in ("Breitung", "Hohenbichler", "Tvedt"):
    sorm = problem.solve("SORM", backend="openturns", correction=correction)
    assert np.isclose(sorm.pf, external.pf, rtol=1.0e-6)

correlated = RandomVector(
    variables.variables,
    correlation_matrix=[[1.0, 0.4], [0.4, 1.0]],
)
correlated_form = ReliabilityProblem(correlated, lambda x: x[0] - x[1]).solve(
    "FORM", backend="openturns"
)
exact_correlated_beta = 40.0 / np.sqrt(120.0)
assert abs(correlated_form.beta - exact_correlated_beta) <= 3.0e-4

standard = RandomVector(
    [
        RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
        RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
    ]
)
nonlinear = LimitStateFunction(lambda x: 3.0 - x[0] + 0.1 * x[1] ** 2)
for correction in ("Breitung", "Hohenbichler", "Tvedt"):
    native_sorm = SORM(standard, nonlinear).solve(correction)
    external_sorm = ReliabilityProblem(standard, nonlinear).solve(
        "SORM", backend="openturns", correction=correction
    )
    assert abs(np.log10(external_sorm.pf) - np.log10(native_sorm.pf)) < 1.5
print(
    {
        "openturns_version": external.metadata["backend_version"],
        "rs_form_beta": external.beta,
        "correlated_form_beta": correlated_form.beta,
    }
)
