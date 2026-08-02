"""Installed-dependency validation matrix for the UQpy adapter."""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy import stats
from uqra import (
    Capability,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
    SamplingResult,
    UQpyBackend,
    get_backend,
    to_uqpy_distribution,
    uqpy_available,
)

pytestmark = [
    pytest.mark.uqpy,
    pytest.mark.skipif(
        os.environ.get("UQRA_TEST_UQPY") != "1",
        reason="set UQRA_TEST_UQPY=1 to run optional backend tests",
    ),
]


def rs_problem(correlation: float = 0.0) -> ReliabilityProblem:
    variables = RandomVector(
        [
            RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
            RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
        ],
        correlation_matrix=[[1.0, correlation], [correlation, 1.0]],
    )
    return ReliabilityProblem(variables, lambda x: x[0] - x[1])


def test_backend_registration_and_capabilities() -> None:
    backend = get_backend("uqpy")

    assert isinstance(backend, UQpyBackend)
    assert uqpy_available()
    assert backend.is_available()
    assert backend.supports(Capability.SAMPLING_LATIN_HYPERCUBE)
    assert backend.supports(Capability.RELIABILITY_SORM)
    assert not backend.supports(Capability.DISTRIBUTION_WEIBULL)


@pytest.mark.parametrize(
    ("variable", "mean", "variance"),
    [
        (RandomVariable("N", "Normal", {"mean": 2.0, "std": 3.0}), 2.0, 9.0),
        (
            RandomVariable("L", "Lognormal", {"mean": 10.0, "std": 2.0}),
            10.0,
            4.0,
        ),
        (RandomVariable("U", "Uniform", {"lower": 2.0, "upper": 6.0}), 4.0, 4 / 3),
    ],
)
def test_distribution_conversion_preserves_moments(
    variable: RandomVariable, mean: float, variance: float
) -> None:
    distribution = to_uqpy_distribution(variable)
    actual_mean, actual_variance = distribution.moments(moments2return="mv")

    assert actual_mean == pytest.approx(mean)
    assert actual_variance == pytest.approx(variance)


@pytest.mark.parametrize("method", ["MC", "LHS"])
def test_sampling_is_reproducible_and_normalized(method: str) -> None:
    backend = get_backend("uqpy")
    first = backend.sample(method, 3, 32, random_state=42)  # type: ignore[attr-defined]
    second = backend.sample(method, 3, 32, random_state=42)  # type: ignore[attr-defined]

    assert isinstance(first, SamplingResult)
    assert first.samples.shape == (32, 3)
    assert first.samples == pytest.approx(second.samples)
    assert np.all((first.samples >= 0.0) & (first.samples <= 1.0))
    assert first.metadata["backend"] == "uqpy"
    if method == "LHS":
        bins = np.floor(first.samples * 32).astype(int)
        assert all(np.unique(bins[:, column]).size == 32 for column in range(3))


def test_rs_form_matches_analytical_and_native_results() -> None:
    problem = rs_problem()
    exact_beta = 40.0 / np.sqrt(200.0)
    native = problem.solve("FORM", backend="native")
    result = problem.solve("FORM", backend="uqpy")

    assert result.beta == pytest.approx(exact_beta, abs=4e-3)
    assert result.pf == pytest.approx(stats.norm.cdf(-exact_beta), abs=3e-5)
    assert result.beta == pytest.approx(native.beta, abs=4e-3)
    assert result.metadata["backend"] == "uqpy"
    assert result.metadata["backend_version"]
    assert result.metadata["algorithm"] == "FORM"


def test_correlated_gaussian_form_preserves_correlation() -> None:
    result = rs_problem(correlation=0.4).solve("FORM", backend="uqpy")
    exact_beta = 40.0 / np.sqrt(120.0)

    assert result.beta == pytest.approx(exact_beta, abs=8e-3)


def test_linear_sorm_reduces_to_form() -> None:
    problem = rs_problem()
    form = problem.solve("FORM", backend="uqpy")
    sorm = problem.solve("SORM", backend="uqpy")

    assert sorm.pf == pytest.approx(form.pf, rel=2e-3)
    assert sorm.metadata["algorithm"] == "SORM"


def test_nonlinear_sorm_has_same_probability_order_as_native() -> None:
    variables = RandomVector(
        [
            RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )
    problem = ReliabilityProblem(
        variables,
        lambda x: 3.0 - (x[0] + x[1]) / np.sqrt(2.0) + 0.1 * (x[0] - x[1]) ** 2,
    )
    native = problem.solve("SORM", backend="native")
    external = problem.solve("SORM", backend="uqpy")

    assert 0.0 < external.pf < 1.0
    assert abs(np.log10(external.pf) - np.log10(native.pf)) < 1.5
