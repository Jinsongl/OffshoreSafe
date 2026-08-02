"""Run the optional Chaospy PCE compatibility benchmark."""

from __future__ import annotations

import numpy as np
from uqra import RandomVariable, RandomVector, get_backend

backend = get_backend("chaospy")
quadratic_variables = RandomVector(
    [
        RandomVariable("x", "Uniform", {"lower": -1.0, "upper": 1.0}),
        RandomVariable("y", "Uniform", {"lower": -1.0, "upper": 1.0}),
    ]
)


def quadratic(point: np.ndarray) -> float:
    x, y = point
    return float(1.0 + 2.0 * x - 0.5 * y + x * y + y**2)


quadrature = backend.fit_surrogate(  # type: ignore[attr-defined]
    quadratic, quadratic_variables, order=2
)
regression = backend.fit_surrogate(  # type: ignore[attr-defined]
    quadratic,
    quadratic_variables,
    order=2,
    fit="regression",
    n_samples=24,
    random_state=42,
)
validation = np.array([[-0.8, 0.2], [0.1, -0.7], [0.9, 0.4]])
expected = np.array([quadratic(point) for point in validation])
assert np.allclose(quadrature.predict(validation), expected, atol=1.0e-10)
assert np.allclose(regression.predict(validation), expected, atol=1.0e-10)

ishigami_variables = RandomVector(
    [
        RandomVariable(name, "Uniform", {"lower": -np.pi, "upper": np.pi})
        for name in ("x1", "x2", "x3")
    ]
)


def ishigami(point: np.ndarray) -> float:
    x1, x2, x3 = point
    return float(np.sin(x1) + 7.0 * np.sin(x2) ** 2 + 0.1 * x3**4 * np.sin(x1))


ishigami_pce = backend.fit_surrogate(  # type: ignore[attr-defined]
    ishigami, ishigami_variables, order=9, quadrature_order=10
)
analytical_variance = (
    0.5 + 7.0**2 / 8.0 + 0.1 * np.pi**4 / 5.0 + 0.1**2 * np.pi**8 / 18.0
)
assert abs(float(ishigami_pce.statistics["mean"]) - 3.5) <= 1.0e-6
assert abs(float(ishigami_pce.statistics["variance"]) - analytical_variance) <= 0.01
print(
    {
        "chaospy_version": ishigami_pce.metadata["backend_version"],
        "quadratic_basis_size": quadrature.metadata["basis_size"],
        "ishigami_mean": float(ishigami_pce.statistics["mean"]),
        "ishigami_variance": float(ishigami_pce.statistics["variance"]),
    }
)
