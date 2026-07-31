"""Standard-normal transformations shared by reliability solvers."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats

from uqra.core import Lognormal, Normal, RandomVector, Uniform, Weibull
from uqra.core.distribution import Distribution
from uqra.core.variable import RandomVariable


def distribution_from_variable(variable: RandomVariable) -> Distribution:
    """Build a native distribution from a RandomVariable definition."""
    key = variable.distribution.casefold().replace("-", "").replace("_", "")
    classes = {
        "normal": Normal,
        "gaussian": Normal,
        "lognormal": Lognormal,
        "weibull": Weibull,
        "uniform": Uniform,
    }
    try:
        distribution_class = classes[key]
    except KeyError as error:
        raise ValueError(
            f"unsupported native distribution: {variable.distribution}"
        ) from error
    try:
        return distribution_class(**variable.parameters)
    except TypeError as error:
        raise ValueError(
            f"invalid parameters for {variable.distribution}: {variable.parameters}"
        ) from error


class GaussianTransform:
    """Gaussian-copula transform from independent normal to physical space."""

    def __init__(self, variables: RandomVector) -> None:
        self.variables = variables
        self.distributions = tuple(
            distribution_from_variable(variable) for variable in variables.variables
        )
        eigenvalues, eigenvectors = np.linalg.eigh(variables.correlation_matrix)
        if np.min(eigenvalues) <= 1e-12:
            raise ValueError("FORM/SORM require a positive-definite correlation matrix")
        self._root = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T

    def to_physical(self, standard_normal: ArrayLike) -> NDArray[np.float64]:
        samples = np.asarray(standard_normal, dtype=float)
        if samples.shape[-1] != self.variables.dimension:
            raise ValueError("last sample dimension does not match RandomVector")
        correlated = samples @ self._root.T
        probabilities = np.clip(stats.norm.cdf(correlated), 1e-14, 1.0 - 1e-14)
        columns = [
            distribution.ppf(probabilities[..., index])
            for index, distribution in enumerate(self.distributions)
        ]
        return np.stack(columns, axis=-1).astype(float, copy=False)


__all__ = ["GaussianTransform", "distribution_from_variable"]
