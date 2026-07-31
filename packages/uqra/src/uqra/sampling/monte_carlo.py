"""Independent pseudo-random Monte Carlo sampling."""

from __future__ import annotations

import numpy as np

from uqra.core.distribution import RandomState
from uqra.sampling.base import Sampler, SamplingResult


class MonteCarloSampler(Sampler):
    """Generate independent uniform samples in the unit hypercube."""

    method = "monte_carlo"

    def sample(
        self, n_samples: int, random_state: RandomState = None
    ) -> SamplingResult:
        self._validate_n_samples(n_samples)
        generator = (
            random_state
            if isinstance(random_state, np.random.Generator)
            else np.random.default_rng(random_state)
        )
        samples = generator.random((n_samples, self.dimension))
        return self._result(samples, n_samples)


__all__ = ["MonteCarloSampler"]
