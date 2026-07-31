"""Crude Monte Carlo reliability analysis."""

from __future__ import annotations

import numpy as np
from scipy import stats

from uqra.core import RandomVector
from uqra.reliability.limit_state import LimitStateFunction
from uqra.reliability.result import ReliabilityResult
from uqra.reliability.transform import GaussianTransform


class MonteCarloReliability:
    """Estimate failure probability by independent random sampling."""

    def __init__(self, variables: RandomVector, limit_state: LimitStateFunction):
        self.variables = variables
        self.limit_state = limit_state
        self._transform = GaussianTransform(variables)

    def solve(
        self,
        n_samples: int = 10_000,
        *,
        random_state: int | np.random.Generator | None = None,
        confidence_level: float = 0.95,
    ) -> ReliabilityResult:
        if not isinstance(n_samples, int) or n_samples <= 0:
            raise ValueError("n_samples must be a positive integer")
        if not 0.0 < confidence_level < 1.0:
            raise ValueError("confidence_level must be between 0 and 1")
        rng = np.random.default_rng(random_state)
        samples = self._transform.to_physical(
            rng.standard_normal((n_samples, self.variables.dimension))
        )
        failures = int(
            np.count_nonzero(self.limit_state.evaluate_samples(samples) <= 0.0)
        )
        pf = failures / n_samples
        beta = float(-stats.norm.ppf(pf))
        z = float(stats.norm.ppf(0.5 + confidence_level / 2.0))
        denominator = 1.0 + z * z / n_samples
        center = (pf + z * z / (2.0 * n_samples)) / denominator
        radius = (
            z
            / denominator
            * np.sqrt(pf * (1.0 - pf) / n_samples + z * z / (4.0 * n_samples**2))
        )
        return ReliabilityResult(
            pf=pf,
            beta=beta,
            method="Monte Carlo",
            confidence_interval=(float(center - radius), float(center + radius)),
            metadata={
                "n_samples": n_samples,
                "n_failures": failures,
                "confidence_level": confidence_level,
            },
        )
