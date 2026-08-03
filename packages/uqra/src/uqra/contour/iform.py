"""Inverse first-order reliability method environmental contours."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats

from uqra.core import RandomVector
from uqra.reliability.transform import GaussianTransform


@dataclass(frozen=True, slots=True)
class IFORMContourResult:
    """Immutable standard-normal and physical IFORM contour points."""

    beta: float
    exceedance_probability: float
    standard_normal_points: NDArray[np.float64]
    physical_points: NDArray[np.float64]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        standard = np.array(self.standard_normal_points, dtype=float, copy=True)
        physical = np.array(self.physical_points, dtype=float, copy=True)
        if standard.ndim != 2 or physical.shape != standard.shape:
            raise ValueError(
                "IFORM point arrays must have the same two-dimensional shape"
            )
        if not np.all(np.isfinite(standard)) or not np.all(np.isfinite(physical)):
            raise ValueError("IFORM points must be finite")
        standard.setflags(write=False)
        physical.setflags(write=False)
        object.__setattr__(self, "standard_normal_points", standard)
        object.__setattr__(self, "physical_points", physical)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class IFORMContour:
    """Generate constant-reliability-radius contours for a RandomVector."""

    def __init__(self, variables: RandomVector) -> None:
        if not isinstance(variables, RandomVector):
            raise TypeError("variables must be a RandomVector")
        if variables.dimension < 2:
            raise ValueError("IFORM contours require at least two variables")
        self.variables = variables
        self.transform = GaussianTransform(variables)

    def generate(
        self,
        return_period: float,
        *,
        events_per_period: float = 1.0,
        n_points: int = 360,
        directions: ArrayLike | None = None,
    ) -> IFORMContourResult:
        """Generate a physical contour for the requested return period."""

        if not math.isfinite(return_period) or return_period <= 1.0:
            raise ValueError("return_period must be finite and greater than one")
        if not math.isfinite(events_per_period) or events_per_period <= 0.0:
            raise ValueError("events_per_period must be finite and positive")
        if isinstance(n_points, bool) or not isinstance(n_points, int) or n_points < 4:
            raise ValueError("n_points must be an integer of at least four")
        exceedance = 1.0 / (return_period * events_per_period)
        if not 0.0 < exceedance < 0.5:
            raise ValueError(
                "return period and event rate must imply probability below 0.5"
            )
        beta = float(stats.norm.ppf(1.0 - exceedance))

        if directions is None:
            if self.variables.dimension != 2:
                raise ValueError(
                    "directions are required for IFORM contours above two dimensions"
                )
            angles = np.linspace(0.0, 2.0 * np.pi, n_points, endpoint=False)
            unit_directions = np.column_stack((np.cos(angles), np.sin(angles)))
        else:
            unit_directions = np.asarray(directions, dtype=float)
            if (
                unit_directions.ndim != 2
                or unit_directions.shape[1] != self.variables.dimension
            ):
                raise ValueError("directions must have shape (n_points, dimension)")
            if not np.all(np.isfinite(unit_directions)):
                raise ValueError("directions must be finite")
            norms = np.linalg.norm(unit_directions, axis=1)
            if np.any(norms <= 0.0):
                raise ValueError("directions must be non-zero")
            unit_directions = unit_directions / norms[:, None]
        standard = beta * unit_directions
        physical = self.transform.to_physical(standard)
        return IFORMContourResult(
            beta=beta,
            exceedance_probability=exceedance,
            standard_normal_points=standard,
            physical_points=physical,
            metadata={
                "method": "IFORM",
                "return_period": return_period,
                "events_per_period": events_per_period,
                "n_points": standard.shape[0],
                "dimension": self.variables.dimension,
            },
        )


__all__ = ["IFORMContour", "IFORMContourResult"]
