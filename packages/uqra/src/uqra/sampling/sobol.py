"""Sobol low-discrepancy sequence sampling."""

from __future__ import annotations

import math

from scipy.stats import qmc  # type: ignore[import-untyped]

from uqra.core.distribution import RandomState
from uqra.sampling.base import Sampler, SamplingResult


class SobolSampler(Sampler):
    """Generate scrambled Sobol points in the unit hypercube."""

    method = "sobol"

    def sample(
        self, n_samples: int, random_state: RandomState = None
    ) -> SamplingResult:
        self._validate_n_samples(n_samples)
        engine = qmc.Sobol(d=self.dimension, scramble=True, seed=random_state)
        power_of_two = n_samples & (n_samples - 1) == 0
        samples = (
            engine.random_base2(int(math.log2(n_samples)))
            if power_of_two
            else engine.random(n_samples)
        )
        return self._result(
            samples,
            n_samples,
            scramble=True,
            balance_guaranteed=power_of_two,
        )


__all__ = ["SobolSampler"]
