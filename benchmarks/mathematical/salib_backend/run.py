"""Run the optional SALib sensitivity compatibility benchmark."""

from __future__ import annotations

import numpy as np
from uqra import RandomVariable, RandomVector, get_backend

backend = get_backend("salib")
ishigami_variables = RandomVector(
    [
        RandomVariable(name, "Uniform", {"lower": -np.pi, "upper": np.pi})
        for name in ("x1", "x2", "x3")
    ]
)


def ishigami(point: np.ndarray) -> float:
    x1, x2, x3 = point
    return float(np.sin(x1) + 7.0 * np.sin(x2) ** 2 + 0.1 * x3**4 * np.sin(x1))


sobol = backend.analyze_sensitivity(  # type: ignore[attr-defined]
    ishigami,
    "Sobol",
    variables=ishigami_variables,
    n_samples=4096,
    random_state=42,
)
assert np.allclose(sobol.indices["S1"], [0.313905, 0.442411, 0.0], atol=0.025)
assert np.allclose(sobol.indices["ST"], [0.557589, 0.442411, 0.243684], atol=0.025)

morris_variables = RandomVector(
    [
        RandomVariable(name, "Uniform", {"lower": 0.0, "upper": 1.0})
        for name in ("dominant", "secondary", "minor")
    ]
)


def weighted_linear(point: np.ndarray) -> float:
    return float(10.0 * point[0] + 3.0 * point[1] + 0.5 * point[2])


options = {
    "variables": morris_variables,
    "n_samples": 64,
    "random_state": 17,
    "num_levels": 8,
}
first = backend.analyze_sensitivity(  # type: ignore[attr-defined]
    weighted_linear, "Morris", **options
)
second = backend.analyze_sensitivity(  # type: ignore[attr-defined]
    weighted_linear, "Morris", **options
)
assert first.indices["ranking"] == ("dominant", "secondary", "minor")
assert np.array_equal(first.indices["mu_star"], second.indices["mu_star"])
print(
    {
        "salib_version": sobol.metadata["backend_version"],
        "ishigami_s1": sobol.indices["S1"].tolist(),
        "ishigami_st": sobol.indices["ST"].tolist(),
        "morris_ranking": first.indices["ranking"],
    }
)
