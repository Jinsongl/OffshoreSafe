"""Unit and benchmark tests for the RandomVector model."""

from __future__ import annotations

import numpy as np
import pytest
from uqra import RandomVariable, RandomVector


def variables(count: int = 2) -> list[RandomVariable]:
    return [RandomVariable(f"X{index}", "Normal") for index in range(count)]


def test_independent_vector_uses_identity_correlation() -> None:
    vector = RandomVector(variables())

    assert vector.dimension == 2
    assert vector.names == ("X0", "X1")
    assert vector.correlation_matrix == pytest.approx(np.eye(2))
    assert vector.covariance_matrix is None


def test_covariance_matrix_derives_correlation_matrix() -> None:
    covariance = np.array([[4.0, 3.0], [3.0, 9.0]])
    vector = RandomVector(variables(), covariance_matrix=covariance)
    covariance[0, 0] = 100.0

    assert vector.covariance_matrix == pytest.approx(
        np.array([[4.0, 3.0], [3.0, 9.0]])
    )
    assert vector.correlation_matrix == pytest.approx(
        np.array([[1.0, 0.5], [0.5, 1.0]])
    )


def test_copula_and_transformation_are_extension_points() -> None:
    copula = object()
    transformation = object()
    vector = RandomVector(
        variables(), copula=copula, transformation=transformation
    )

    assert vector.copula is copula
    assert vector.transformation is transformation


def test_gaussian_correlation_benchmark() -> None:
    """Recover the configured Gaussian correlation within sampling tolerance."""
    target = np.array([[1.0, 0.7], [0.7, 1.0]])
    vector = RandomVector(variables(), correlation_matrix=target)
    independent = np.random.default_rng(20260731).standard_normal((100_000, 2))

    correlated = vector.correlate(independent)

    assert np.corrcoef(correlated, rowvar=False) == pytest.approx(target, abs=0.01)


@pytest.mark.parametrize(
    ("matrix", "message"),
    [
        ([[1.0]], "must have shape"),
        ([[1.0, 0.2], [0.1, 1.0]], "must be symmetric"),
        ([[1.0, 2.0], [2.0, 1.0]], "positive semidefinite"),
        ([[2.0, 0.0], [0.0, 2.0]], "diagonal must contain ones"),
    ],
)
def test_invalid_correlation_matrix_is_rejected(
    matrix: list[list[float]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        RandomVector(variables(), correlation_matrix=matrix)


def test_vector_requires_unique_random_variables() -> None:
    duplicate = RandomVariable("X", "Normal")

    with pytest.raises(ValueError, match="names must be unique"):
        RandomVector([duplicate, duplicate])


def test_vector_rejects_two_dependence_matrices() -> None:
    with pytest.raises(ValueError, match="cannot both be provided"):
        RandomVector(
            variables(),
            correlation_matrix=np.eye(2),
            covariance_matrix=np.eye(2),
        )


def test_correlate_validates_sample_shape() -> None:
    with pytest.raises(ValueError, match="n_samples, dimension"):
        RandomVector(variables()).correlate([1.0, 2.0])
