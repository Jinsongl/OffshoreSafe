"""Installed-dependency validation for the SALib sensitivity adapter."""

from __future__ import annotations

import os

import numpy as np
import pytest
from uqra import (
    Capability,
    RandomVariable,
    RandomVector,
    SALibBackend,
    SensitivityResult,
    get_backend,
    salib_available,
    to_salib_problem,
)

pytestmark = [
    pytest.mark.salib,
    pytest.mark.skipif(
        os.environ.get("UQRA_TEST_SALIB") != "1",
        reason="set UQRA_TEST_SALIB=1 to run optional backend tests",
    ),
]


def uniform_variables(
    names: tuple[str, ...], lower: float, upper: float
) -> RandomVector:
    return RandomVector(
        [
            RandomVariable(name, "Uniform", {"lower": lower, "upper": upper})
            for name in names
        ]
    )


def ishigami(point: np.ndarray) -> float:
    x1, x2, x3 = point
    return float(np.sin(x1) + 7.0 * np.sin(x2) ** 2 + 0.1 * x3**4 * np.sin(x1))


def test_backend_registration_and_capabilities() -> None:
    backend = get_backend("salib")

    assert isinstance(backend, SALibBackend)
    assert salib_available()
    assert backend.is_available()
    assert backend.supports(Capability.SENSITIVITY_SOBOL)
    assert backend.supports(Capability.SENSITIVITY_MORRIS)


def test_problem_conversion_preserves_names_and_bounds() -> None:
    variables = uniform_variables(("a", "b"), -2.0, 3.0)

    assert to_salib_problem(variables) == {
        "num_vars": 2,
        "names": ["a", "b"],
        "bounds": [[-2.0, 3.0], [-2.0, 3.0]],
    }


def test_ishigami_sobol_indices_match_analytical_values() -> None:
    variables = uniform_variables(("x1", "x2", "x3"), -np.pi, np.pi)
    result = get_backend("salib").analyze_sensitivity(  # type: ignore[attr-defined]
        ishigami,
        "Sobol",
        variables=variables,
        n_samples=4096,
        random_state=42,
    )

    assert isinstance(result, SensitivityResult)
    assert result.indices["S1"] == pytest.approx([0.313905, 0.442411, 0.0], abs=0.025)
    assert result.indices["ST"] == pytest.approx(
        [0.557589, 0.442411, 0.243684], abs=0.025
    )
    assert result.indices["names"] == ("x1", "x2", "x3")
    assert result.metadata["backend"] == "salib"
    assert result.metadata["algorithm"] == "Sobol"


def test_morris_ranking_and_reproducibility() -> None:
    variables = uniform_variables(("dominant", "secondary", "minor"), 0.0, 1.0)

    def weighted_linear(point: np.ndarray) -> float:
        return float(10.0 * point[0] + 3.0 * point[1] + 0.5 * point[2])

    options = {
        "variables": variables,
        "n_samples": 64,
        "random_state": 17,
        "num_levels": 8,
    }
    backend = get_backend("salib")
    first = backend.analyze_sensitivity(  # type: ignore[attr-defined]
        weighted_linear, "Morris", **options
    )
    second = backend.analyze_sensitivity(  # type: ignore[attr-defined]
        weighted_linear, "Morris", **options
    )

    assert first.indices["ranking"] == ("dominant", "secondary", "minor")
    assert first.indices["mu_star"] == pytest.approx(second.indices["mu_star"])
    assert first.indices["mu_star_conf"] == pytest.approx(
        second.indices["mu_star_conf"]
    )
    assert first.metadata["model_evaluations"] == 64 * 4


def test_nonuniform_and_correlated_inputs_are_rejected() -> None:
    nonuniform = RandomVector(
        [RandomVariable("x", "Normal", {"mean": 0.0, "std": 1.0})]
    )
    correlated = RandomVector(
        uniform_variables(("x", "y"), 0.0, 1.0).variables,
        correlation_matrix=[[1.0, 0.2], [0.2, 1.0]],
    )

    with pytest.raises(ValueError, match="Uniform"):
        to_salib_problem(nonuniform)
    with pytest.raises(ValueError, match="independent"):
        to_salib_problem(correlated)
