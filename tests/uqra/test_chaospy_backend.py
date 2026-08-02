"""Installed-dependency validation for the Chaospy PCE adapter."""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy import special
from uqra import (
    Capability,
    ChaospyBackend,
    RandomVariable,
    RandomVector,
    SurrogateResult,
    chaospy_available,
    get_backend,
    to_chaospy_distribution,
)

pytestmark = [
    pytest.mark.chaospy,
    pytest.mark.skipif(
        os.environ.get("UQRA_TEST_CHAOSPY") != "1",
        reason="set UQRA_TEST_CHAOSPY=1 to run optional backend tests",
    ),
]


def polynomial_variables() -> RandomVector:
    return RandomVector(
        [
            RandomVariable("x", "Uniform", {"lower": -1.0, "upper": 1.0}),
            RandomVariable("y", "Uniform", {"lower": -1.0, "upper": 1.0}),
        ]
    )


def polynomial_model(x: np.ndarray) -> float:
    return float(1.0 + 2.0 * x[0] - 0.5 * x[1] + x[0] * x[1] + x[1] ** 2)


def test_backend_registration_and_capabilities() -> None:
    backend = get_backend("chaospy")

    assert isinstance(backend, ChaospyBackend)
    assert chaospy_available()
    assert backend.is_available()
    assert backend.supports(Capability.SURROGATE_PCE)
    assert backend.supports(Capability.DISTRIBUTION_WEIBULL)


@pytest.mark.parametrize(
    ("variable", "mean", "variance"),
    [
        (RandomVariable("N", "Normal", {"mean": 2.0, "std": 3.0}), 2.0, 9.0),
        (
            RandomVariable("L", "Lognormal", {"mean": 10.0, "std": 2.0}),
            10.0,
            4.0,
        ),
        (
            RandomVariable("W", "Weibull", {"shape": 2.0, "scale": 5.0}),
            5.0 * special.gamma(1.5),
            25.0 * (special.gamma(2.0) - special.gamma(1.5) ** 2),
        ),
        (RandomVariable("U", "Uniform", {"lower": 2.0, "upper": 6.0}), 4.0, 4 / 3),
    ],
)
def test_distribution_conversion_preserves_moments(
    variable: RandomVariable, mean: float, variance: float
) -> None:
    distribution = to_chaospy_distribution(variable)

    assert float(distribution.mom(1)) == pytest.approx(mean)
    assert float(distribution.mom(2) - distribution.mom(1) ** 2) == pytest.approx(
        variance
    )


def test_quadrature_pce_exactly_recovers_quadratic_model() -> None:
    result = get_backend("chaospy").fit_surrogate(  # type: ignore[attr-defined]
        polynomial_model, polynomial_variables(), "PCE", order=2
    )
    points = np.array([[-0.8, 0.2], [0.1, -0.7], [0.9, 0.4]])
    exact = np.array([polynomial_model(point) for point in points])

    assert isinstance(result, SurrogateResult)
    assert result.predict(points) == pytest.approx(exact, abs=1e-10)
    assert result.statistics["mean"] == pytest.approx(4 / 3, abs=1e-10)
    assert result.metadata["fit"] == "quadrature"
    assert result.metadata["backend"] == "chaospy"


def test_regression_pce_is_reproducible_and_exact_for_quadratic() -> None:
    backend = get_backend("chaospy")
    first = backend.fit_surrogate(  # type: ignore[attr-defined]
        polynomial_model,
        polynomial_variables(),
        order=2,
        fit="regression",
        n_samples=24,
        random_state=42,
    )
    second = backend.fit_surrogate(  # type: ignore[attr-defined]
        polynomial_model,
        polynomial_variables(),
        order=2,
        fit="regression",
        n_samples=24,
        random_state=42,
    )
    points = np.array([[-0.3, 0.4], [0.75, -0.2]])

    assert first.predict(points) == pytest.approx(second.predict(points))
    assert first.predict(points) == pytest.approx(
        [polynomial_model(point) for point in points], abs=1e-10
    )


def test_pce_rejects_correlated_variables_explicitly() -> None:
    variables = RandomVector(
        polynomial_variables().variables,
        correlation_matrix=[[1.0, 0.3], [0.3, 1.0]],
    )

    with pytest.raises(ValueError, match="independent variables"):
        get_backend("chaospy").fit_surrogate(  # type: ignore[attr-defined]
            polynomial_model, variables, order=2
        )
