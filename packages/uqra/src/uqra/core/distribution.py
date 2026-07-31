"""Backend-independent probability distribution interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeAlias

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats  # type: ignore[import-untyped]

NumericResult: TypeAlias = float | NDArray[np.float64]
SampleShape: TypeAlias = int | tuple[int, ...]
RandomState: TypeAlias = int | np.random.Generator | None


class Distribution(ABC):
    """Common interface implemented by all UQRA distributions."""

    @abstractmethod
    def pdf(self, x: ArrayLike) -> NumericResult:
        """Evaluate the probability density function at *x*."""

    @abstractmethod
    def cdf(self, x: ArrayLike) -> NumericResult:
        """Evaluate the cumulative distribution function at *x*."""

    @abstractmethod
    def ppf(self, probability: ArrayLike) -> NumericResult:
        """Evaluate the inverse cumulative distribution function."""

    @abstractmethod
    def sample(
        self, size: SampleShape = 1, random_state: RandomState = None
    ) -> NDArray[np.float64]:
        """Draw samples with a reproducible optional random state."""


class _ScipyDistribution(Distribution):
    """Shared implementation for continuous SciPy-backed distributions."""

    _distribution: stats.rv_continuous_frozen

    def pdf(self, x: ArrayLike) -> NumericResult:
        return self._distribution.pdf(x)

    def cdf(self, x: ArrayLike) -> NumericResult:
        return self._distribution.cdf(x)

    def ppf(self, probability: ArrayLike) -> NumericResult:
        probabilities = np.asarray(probability)
        if np.any((probabilities < 0.0) | (probabilities > 1.0)):
            raise ValueError("probability must be between 0 and 1")
        return self._distribution.ppf(probability)

    def sample(
        self, size: SampleShape = 1, random_state: RandomState = None
    ) -> NDArray[np.float64]:
        if isinstance(size, int):
            if size < 0:
                raise ValueError("size must be non-negative")
        elif not (
            isinstance(size, tuple)
            and all(isinstance(length, int) and length >= 0 for length in size)
        ):
            raise TypeError("size must be a non-negative integer or tuple of integers")
        return np.asarray(
            self._distribution.rvs(size=size, random_state=random_state),
            dtype=float,
        )


class Normal(_ScipyDistribution):
    """Normal distribution parameterized by arithmetic mean and standard deviation."""

    def __init__(self, mean: float = 0.0, std: float = 1.0) -> None:
        if std <= 0.0:
            raise ValueError("std must be positive")
        self.mean = float(mean)
        self.std = float(std)
        self._distribution = stats.norm(loc=self.mean, scale=self.std)


class Lognormal(_ScipyDistribution):
    """Lognormal distribution parameterized by arithmetic mean and standard deviation."""

    def __init__(self, mean: float, std: float) -> None:
        if mean <= 0.0:
            raise ValueError("mean must be positive")
        if std <= 0.0:
            raise ValueError("std must be positive")
        self.mean = float(mean)
        self.std = float(std)
        variance_ratio = (self.std / self.mean) ** 2
        sigma = np.sqrt(np.log1p(variance_ratio))
        scale = self.mean / np.sqrt(1.0 + variance_ratio)
        self._distribution = stats.lognorm(s=sigma, scale=scale)


class Weibull(_ScipyDistribution):
    """Two-parameter Weibull distribution."""

    def __init__(self, scale: float, shape: float) -> None:
        if scale <= 0.0:
            raise ValueError("scale must be positive")
        if shape <= 0.0:
            raise ValueError("shape must be positive")
        self.scale = float(scale)
        self.shape = float(shape)
        self._distribution = stats.weibull_min(c=self.shape, scale=self.scale)


class Uniform(_ScipyDistribution):
    """Continuous uniform distribution on the closed interval [lower, upper]."""

    def __init__(self, lower: float, upper: float) -> None:
        if upper <= lower:
            raise ValueError("upper must be greater than lower")
        self.lower = float(lower)
        self.upper = float(upper)
        self._distribution = stats.uniform(
            loc=self.lower,
            scale=self.upper - self.lower,
        )


__all__ = ["Distribution", "Lognormal", "Normal", "Uniform", "Weibull"]
