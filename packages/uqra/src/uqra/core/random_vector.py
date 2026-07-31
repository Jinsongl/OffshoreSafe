"""Random-vector data model."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from uqra.core.variable import RandomVariable


class RandomVector:
    """Group random variables and their linear dependence information.

    Exactly one of ``correlation_matrix`` and ``covariance_matrix`` may be
    supplied. If neither is supplied, variables are treated as independent.
    ``copula`` and ``transformation`` are extension points for later modules.
    """

    def __init__(
        self,
        variables: Iterable[RandomVariable],
        correlation_matrix: ArrayLike | None = None,
        *,
        covariance_matrix: ArrayLike | None = None,
        copula: Any | None = None,
        transformation: Any | None = None,
    ) -> None:
        self.variables = tuple(variables)
        if not self.variables:
            raise ValueError("variables must contain at least one RandomVariable")
        if not all(isinstance(variable, RandomVariable) for variable in self.variables):
            raise TypeError("variables must contain only RandomVariable objects")
        names = [variable.name for variable in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("variable names must be unique")
        if correlation_matrix is not None and covariance_matrix is not None:
            raise ValueError(
                "correlation_matrix and covariance_matrix cannot both be provided"
            )

        dimension = len(self.variables)
        if covariance_matrix is not None:
            covariance = self._validate_matrix(
                covariance_matrix, dimension, "covariance_matrix"
            )
            if np.any(np.diag(covariance) <= 0.0):
                raise ValueError("covariance_matrix diagonal must be positive")
            standard_deviations = np.sqrt(np.diag(covariance))
            correlation = covariance / np.outer(
                standard_deviations, standard_deviations
            )
            self._covariance_matrix: NDArray[np.float64] | None = covariance
        else:
            correlation = self._validate_matrix(
                np.eye(dimension) if correlation_matrix is None else correlation_matrix,
                dimension,
                "correlation_matrix",
            )
            if not np.allclose(np.diag(correlation), 1.0):
                raise ValueError("correlation_matrix diagonal must contain ones")
            if np.any(np.abs(correlation) > 1.0 + 1e-12):
                raise ValueError("correlation coefficients must be between -1 and 1")
            self._covariance_matrix = None

        correlation.setflags(write=False)
        if self._covariance_matrix is not None:
            self._covariance_matrix.setflags(write=False)
        self._correlation_matrix = correlation
        self.copula = copula
        self.transformation = transformation

    @staticmethod
    def _validate_matrix(
        matrix: ArrayLike, dimension: int, name: str
    ) -> NDArray[np.float64]:
        values = np.array(matrix, dtype=float, copy=True)
        if values.shape != (dimension, dimension):
            raise ValueError(f"{name} must have shape ({dimension}, {dimension})")
        if not np.all(np.isfinite(values)):
            raise ValueError(f"{name} must contain only finite values")
        if not np.allclose(values, values.T):
            raise ValueError(f"{name} must be symmetric")
        if np.min(np.linalg.eigvalsh(values)) < -1e-12:
            raise ValueError(f"{name} must be positive semidefinite")
        return values

    @property
    def dimension(self) -> int:
        """Number of variables in the vector."""
        return len(self.variables)

    @property
    def names(self) -> tuple[str, ...]:
        """Variable names in vector order."""
        return tuple(variable.name for variable in self.variables)

    @property
    def correlation_matrix(self) -> NDArray[np.float64]:
        """Read-only correlation matrix."""
        return self._correlation_matrix

    @property
    def covariance_matrix(self) -> NDArray[np.float64] | None:
        """Read-only covariance matrix, when explicitly supplied."""
        return self._covariance_matrix

    def correlate(self, independent_standard_normal: ArrayLike) -> NDArray[np.float64]:
        """Transform independent standard-normal rows to the configured correlation."""
        samples = np.asarray(independent_standard_normal, dtype=float)
        if samples.ndim != 2 or samples.shape[1] != self.dimension:
            raise ValueError(
                "independent_standard_normal must have shape (n_samples, dimension)"
            )
        eigenvalues, eigenvectors = np.linalg.eigh(self.correlation_matrix)
        square_root = eigenvectors @ np.diag(np.sqrt(np.clip(eigenvalues, 0.0, None)))
        return samples @ square_root.T


__all__ = ["RandomVector"]
