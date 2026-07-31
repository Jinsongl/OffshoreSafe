"""Shared types and validation for sampling engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import NDArray

from uqra.core.distribution import RandomState


@dataclass(frozen=True, slots=True)
class SamplingResult:
    """Samples and traceable information produced by a sampler."""

    samples: NDArray[np.float64]
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        values = np.array(self.samples, dtype=float, copy=True)
        if values.ndim != 2:
            raise ValueError("samples must be a two-dimensional array")
        values.setflags(write=False)
        object.__setattr__(self, "samples", values)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class Sampler(ABC):
    """Common interface for unit-hypercube sampling engines."""

    method: str

    def __init__(self, dimension: int) -> None:
        if isinstance(dimension, bool) or not isinstance(dimension, int):
            raise TypeError("dimension must be an integer")
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension

    @staticmethod
    def _validate_n_samples(n_samples: int) -> None:
        if isinstance(n_samples, bool) or not isinstance(n_samples, int):
            raise TypeError("n_samples must be an integer")
        if n_samples <= 0:
            raise ValueError("n_samples must be positive")

    def _result(
        self, samples: NDArray[np.float64], n_samples: int, **metadata: Any
    ) -> SamplingResult:
        return SamplingResult(
            samples,
            {
                "method": self.method,
                "n_samples": n_samples,
                "dimension": self.dimension,
                **metadata,
            },
        )

    @abstractmethod
    def sample(
        self, n_samples: int, random_state: RandomState = None
    ) -> SamplingResult:
        """Generate samples in the unit hypercube."""


__all__ = ["Sampler", "SamplingResult"]
