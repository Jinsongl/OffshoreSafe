"""Issue #081 domain-independent IFORM tests."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats
from uqra import IFORMContour, RandomVariable, RandomVector


def test_standard_normal_iform_is_exact_circle() -> None:
    variables = RandomVector(
        [
            RandomVariable("x", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("y", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )
    result = IFORMContour(variables).generate(
        50.0, events_per_period=365.25, n_points=72
    )
    expected_probability = 1.0 / (50.0 * 365.25)
    expected_beta = stats.norm.ppf(1.0 - expected_probability)

    assert result.exceedance_probability == pytest.approx(expected_probability)
    assert result.beta == pytest.approx(expected_beta)
    assert np.linalg.norm(result.standard_normal_points, axis=1) == pytest.approx(
        expected_beta
    )
    assert result.physical_points == pytest.approx(result.standard_normal_points)
    assert result.metadata["method"] == "IFORM"
    with pytest.raises(ValueError):
        result.physical_points[0, 0] = 0.0


def test_correlated_normal_transform_matches_gaussian_root() -> None:
    correlation = np.array([[1.0, 0.4], [0.4, 1.0]])
    variables = RandomVector(
        [
            RandomVariable("x", "Normal", {"mean": 10.0, "std": 2.0}),
            RandomVariable("y", "Normal", {"mean": 20.0, "std": 3.0}),
        ],
        correlation,
    )
    result = IFORMContour(variables).generate(100.0, n_points=8)

    eigenvalues, eigenvectors = np.linalg.eigh(correlation)
    root = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T
    correlated = result.standard_normal_points @ root.T
    expected = np.column_stack(
        (10.0 + 2.0 * correlated[:, 0], 20.0 + 3.0 * correlated[:, 1])
    )
    assert result.physical_points == pytest.approx(expected)


def test_higher_dimensional_contour_accepts_explicit_directions() -> None:
    variables = RandomVector(
        [
            RandomVariable(name, "Normal", {"mean": 0.0, "std": 1.0})
            for name in ("x", "y", "z")
        ]
    )
    directions = [[1, 0, 0], [1, 1, 1], [0, 0, -2]]
    result = IFORMContour(variables).generate(50.0, directions=directions)

    assert result.physical_points.shape == (3, 3)
    assert np.linalg.norm(result.standard_normal_points, axis=1) == pytest.approx(
        result.beta
    )
    with pytest.raises(ValueError, match="directions are required"):
        IFORMContour(variables).generate(50.0)


@pytest.mark.parametrize(
    "options",
    [
        {"return_period": 1.0},
        {"return_period": 50.0, "events_per_period": 0.0},
        {"return_period": 50.0, "n_points": 3},
    ],
)
def test_invalid_iform_inputs_are_rejected(options: dict[str, float]) -> None:
    variables = RandomVector(
        [
            RandomVariable("x", "Normal", {"mean": 0.0, "std": 1.0}),
            RandomVariable("y", "Normal", {"mean": 0.0, "std": 1.0}),
        ]
    )
    with pytest.raises(ValueError):
        IFORMContour(variables).generate(**options)
