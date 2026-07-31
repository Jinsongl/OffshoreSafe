"""Run deterministic Milestone 0.2 probability benchmarks."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

SOURCE_ROOT = Path(__file__).parents[3] / "packages" / "uqra" / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from uqra import Lognormal, Normal, RandomVariable, RandomVector

normal = Normal()
assert np.isclose(normal.pdf(0.0), 0.3989422804014327, atol=1e-12)
assert np.isclose(normal.cdf(0.0), 0.5, atol=1e-12)
assert np.isclose(normal.ppf(0.975), 1.959963984540054, atol=1e-12)

lognormal_samples = Lognormal(mean=10.0, std=2.0).sample(
    200_000, random_state=1234
)
assert np.isclose(np.mean(lognormal_samples), 10.0, rtol=0.01)
assert np.isclose(np.std(lognormal_samples), 2.0, rtol=0.01)

variables = [RandomVariable("X1", "Normal"), RandomVariable("X2", "Normal")]
target_correlation = np.array([[1.0, 0.7], [0.7, 1.0]])
vector = RandomVector(variables, correlation_matrix=target_correlation)
independent = np.random.default_rng(20260731).standard_normal((100_000, 2))
observed_correlation = np.corrcoef(vector.correlate(independent), rowvar=False)
assert np.allclose(observed_correlation, target_correlation, atol=0.01)

print("Core probability benchmark passed.")
