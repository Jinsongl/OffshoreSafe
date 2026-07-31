"""Installed-dependency validation matrix for the OpenTURNS adapter."""

from __future__ import annotations

import os

import numpy as np
import pytest
from scipy import special, stats
from uqra import (
    SORM,
    Capability,
    LimitStateFunction,
    OpenTURNSBackend,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
    get_backend,
    openturns_available,
    to_openturns_distribution,
    to_openturns_joint_distribution,
)

pytestmark = [
    pytest.mark.openturns,
    pytest.mark.skipif(
        os.environ.get("UQRA_TEST_OPENTURNS") != "1",
        reason="set UQRA_TEST_OPENTURNS=1 to run optional backend tests",
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


def four_branch_problem() -> ReliabilityProblem:
    variables = RandomVector(
        [
            RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )

    def four_branch(x: np.ndarray) -> float:
        x1, x2 = x
        return float(
            min(
                3.0 + 0.1 * (x1 - x2) ** 2 - (x1 + x2) / np.sqrt(2.0),
                3.0 + 0.1 * (x1 - x2) ** 2 + (x1 + x2) / np.sqrt(2.0),
                x1 - x2 + 7.0 / np.sqrt(2.0),
                x2 - x1 + 7.0 / np.sqrt(2.0),
            )
        )

    return ReliabilityProblem(variables, four_branch)


def test_backend_is_registered_and_reports_capabilities() -> None:
    backend = get_backend("openturns")

    assert isinstance(backend, OpenTURNSBackend)
    assert openturns_available()
    assert backend.is_available()
    assert backend.supports(Capability.DISTRIBUTION_LOGNORMAL)
    assert backend.supports(Capability.RELIABILITY_SORM)


@pytest.mark.parametrize(
    ("variable", "expected_mean", "expected_std"),
    [
        (RandomVariable("N", "Normal", {"mean": 2.0, "std": 3.0}), 2.0, 3.0),
        (
            RandomVariable("L", "Lognormal", {"mean": 10.0, "std": 2.0}),
            10.0,
            2.0,
        ),
        (
            RandomVariable("W", "Weibull", {"scale": 5.0, "shape": 2.0}),
            5.0 * float(special.gamma(1.5)),
            5.0 * np.sqrt(float(special.gamma(2.0)) - float(special.gamma(1.5)) ** 2),
        ),
        (
            RandomVariable("U", "Uniform", {"lower": 2.0, "upper": 6.0}),
            4.0,
            np.sqrt(4.0 / 3.0),
        ),
    ],
)
def test_supported_distribution_conversion_preserves_moments(
    variable: RandomVariable, expected_mean: float, expected_std: float
) -> None:
    distribution = to_openturns_distribution(variable)

    assert distribution.getMean()[0] == pytest.approx(expected_mean, rel=1e-10)
    assert distribution.getStandardDeviation()[0] == pytest.approx(
        expected_std, rel=1e-10
    )
    assert distribution.getDescription()[0] == variable.name


def test_correlated_gaussian_conversion_preserves_latent_correlation() -> None:
    problem = rs_problem(correlation=0.4)
    distribution = to_openturns_joint_distribution(problem.variables)

    assert np.asarray(distribution.getCorrelation(), dtype=float) == pytest.approx(
        np.array([[1.0, 0.4], [0.4, 1.0]])
    )


def test_rs_form_matches_analytical_and_native_results() -> None:
    problem = rs_problem()
    exact_beta = 40.0 / np.sqrt(200.0)
    native = problem.solve("FORM", backend="native")
    result = problem.solve("FORM", backend="openturns")

    assert result.beta == pytest.approx(exact_beta, abs=2e-4)
    assert result.pf == pytest.approx(stats.norm.cdf(-exact_beta), abs=2e-6)
    assert result.beta == pytest.approx(native.beta, abs=2e-4)
    assert result.metadata["backend"] == "openturns"
    assert result.metadata["backend_version"]
    assert result.metadata["algorithm"] == "FORM"


def test_four_branch_form_matches_nearest_design_point() -> None:
    result = four_branch_problem().solve("FORM", backend="openturns")

    assert result.beta == pytest.approx(3.0, abs=3e-3)
    assert np.linalg.norm(result.standard_normal_design_point) == pytest.approx(
        result.beta, abs=3e-3
    )


@pytest.mark.parametrize("correction", ["Breitung", "Hohenbichler", "Tvedt"])
def test_linear_sorm_reduces_to_form(correction: str) -> None:
    problem = rs_problem()
    form = problem.solve("FORM", backend="openturns")
    sorm = problem.solve("SORM", backend="openturns", correction=correction)

    assert sorm.pf == pytest.approx(form.pf, rel=1e-6)
    assert sorm.metadata["correction"] == correction.casefold()


@pytest.mark.parametrize("correction", ["Breitung", "Hohenbichler", "Tvedt"])
def test_nonlinear_sorm_is_consistent_with_native_order_of_magnitude(
    correction: str,
) -> None:
    variables = RandomVector(
        [
            RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )
    limit_state = LimitStateFunction(lambda x: 3.0 - x[0] + 0.1 * x[1] ** 2)
    native = SORM(variables, limit_state).solve(correction)
    external = ReliabilityProblem(variables, limit_state).solve(
        "SORM", backend="openturns", correction=correction
    )

    assert 0.0 < external.pf < 1.0
    assert abs(np.log10(external.pf) - np.log10(native.pf)) < 1.5
