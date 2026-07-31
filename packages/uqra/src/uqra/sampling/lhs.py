"""Latin Hypercube sampling."""

from __future__ import annotations

from scipy.stats import qmc  # type: ignore[import-untyped]

from uqra.core.distribution import RandomState
from uqra.sampling.base import Sampler, SamplingResult


class LatinHypercubeSampler(Sampler):
    """Generate one randomized point in every one-dimensional stratum."""

    method = "latin_hypercube"

    def sample(
        self, n_samples: int, random_state: RandomState = None
    ) -> SamplingResult:
        self._validate_n_samples(n_samples)
        samples = qmc.LatinHypercube(
            d=self.dimension, scramble=True, seed=random_state
        ).random(n_samples)
        return self._result(samples, n_samples, scramble=True)


LHSSampler = LatinHypercubeSampler

__all__ = ["LHSSampler", "LatinHypercubeSampler"]
