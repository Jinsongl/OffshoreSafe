"""Unit and numerical validation tests for the reliability engine."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats
from uqra import (
    FORM,
    SORM,
    LimitStateFunction,
    MonteCarloReliability,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
    ReliabilityResult,
)


@pytest.fixture
def rs_variables() -> RandomVector:
    return RandomVector(
        [
            RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
            RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
        ]
    )


def test_limit_state_supports_analytical_and_external_models() -> None:
    analytical = LimitStateFunction(lambda x: x[..., 0] - x[..., 1])

    class ExternalModel:
        def evaluate(self, x: np.ndarray) -> float:
            return float(x[0] - x[1])

    external = LimitStateFunction(ExternalModel())
    samples = np.array([[3.0, 2.0], [1.0, 2.0]])

    assert analytical.evaluate_samples(samples) == pytest.approx([1.0, -1.0])
    assert external.evaluate_samples(samples) == pytest.approx([1.0, -1.0])


def test_limit_state_rejects_invalid_model() -> None:
    with pytest.raises(TypeError, match="callable"):
        LimitStateFunction(object())


def test_monte_carlo_rs_probability_and_confidence_interval(
    rs_variables: RandomVector,
) -> None:
    exact_beta = 40.0 / np.sqrt(200.0)
    result = MonteCarloReliability(
        rs_variables, LimitStateFunction(lambda x: x[..., 0] - x[..., 1])
    ).solve(n_samples=200_000, random_state=2026)

    assert isinstance(result, ReliabilityResult)
    assert result.pf == pytest.approx(stats.norm.cdf(-exact_beta), abs=2e-4)
    assert result.confidence_interval[0] <= stats.norm.cdf(-exact_beta)
    assert result.confidence_interval[1] >= stats.norm.cdf(-exact_beta)
    assert result.metadata["n_samples"] == 200_000


def test_form_matches_analytical_rs_solution(rs_variables: RandomVector) -> None:
    exact_beta = 40.0 / np.sqrt(200.0)
    result = FORM(rs_variables, LimitStateFunction(lambda x: x[0] - x[1])).solve()

    assert result.converged
    assert result.beta == pytest.approx(exact_beta, rel=1e-6)
    assert result.pf == pytest.approx(stats.norm.cdf(-exact_beta), rel=1e-6)
    assert result.design_point[0] == pytest.approx(result.design_point[1], abs=1e-5)
    assert np.linalg.norm(result.standard_normal_design_point) == pytest.approx(
        result.beta
    )
    assert np.linalg.norm(result.sensitivity) == pytest.approx(1.0)


def test_form_four_branch_finds_nearest_design_point() -> None:
    variables = RandomVector(
        [
            RandomVariable("u1", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("u2", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )

    def branch(x: np.ndarray) -> float:
        x1, x2 = x
        branches = [
            3.0 + 0.1 * (x1 - x2) ** 2 - (x1 + x2) / np.sqrt(2.0),
            3.0 + 0.1 * (x1 - x2) ** 2 + (x1 + x2) / np.sqrt(2.0),
            (x1 - x2) + 7.0 / np.sqrt(2.0),
            (x2 - x1) + 7.0 / np.sqrt(2.0),
        ]
        return float(min(branches))

    result = FORM(variables, LimitStateFunction(branch)).solve()

    assert result.beta == pytest.approx(3.0, abs=2e-4)
    assert abs(branch(result.design_point)) < 1e-5


@pytest.mark.parametrize("method", ["breitung", "hohenbichler", "tvedt"])
def test_sorm_methods_reduce_to_form_for_linear_limit_state(
    rs_variables: RandomVector, method: str
) -> None:
    limit_state = LimitStateFunction(lambda x: x[0] - x[1])
    form = FORM(rs_variables, limit_state).solve()
    result = SORM(rs_variables, limit_state).solve(method)

    assert result.pf == pytest.approx(form.pf, rel=1e-7)
    assert result.metadata["principal_curvatures"] == pytest.approx([0.0], abs=2e-5)


@pytest.mark.parametrize("method", ["breitung", "hohenbichler", "tvedt"])
def test_sorm_methods_return_finite_probability_for_nonlinear_surface(
    method: str,
) -> None:
    variables = RandomVector(
        [
            RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )
    result = SORM(
        variables,
        LimitStateFunction(lambda x: 3.0 - x[0] - 0.15 * x[1] ** 2),
    ).solve(method)

    assert 0.0 < result.pf < 1.0
    assert np.all(np.isfinite(result.metadata["principal_curvatures"]))


def test_reliability_problem_dispatches_and_retains_result(
    rs_variables: RandomVector,
) -> None:
    problem = ReliabilityProblem(rs_variables, lambda x: x[0] - x[1])
    result = problem.solve("FORM")

    assert result is problem.result
    assert result.Pf == result.pf
    with pytest.raises(ValueError, match="backend"):
        problem.solve("FORM", backend="missing")


def test_invalid_solver_inputs_are_rejected(rs_variables: RandomVector) -> None:
    limit_state = LimitStateFunction(lambda x: x[0] - x[1])
    with pytest.raises(ValueError, match="positive integer"):
        MonteCarloReliability(rs_variables, limit_state).solve(0)
    with pytest.raises(ValueError, match="method must"):
        SORM(rs_variables, limit_state).solve("unknown")
    with pytest.raises(ValueError, match="unsupported"):
        ReliabilityProblem(rs_variables, limit_state).solve("unknown")
