"""Normalized reliability-analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class ReliabilityResult:
    """Backend-independent result returned by reliability solvers."""

    pf: float
    beta: float
    method: str
    confidence_interval: tuple[float, float] | None = None
    design_point: NDArray[np.float64] | None = None
    standard_normal_design_point: NDArray[np.float64] | None = None
    sensitivity: NDArray[np.float64] | None = None
    converged: bool | None = None
    iterations: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def Pf(self) -> float:
        """Compatibility alias matching the notation used by the API design."""
        return self.pf

    @property
    def failure_probability(self) -> float:
        """Long-form alias for ``pf``."""
        return self.pf

    @property
    def reliability_index(self) -> float:
        """Long-form alias for ``beta``."""
        return self.beta
