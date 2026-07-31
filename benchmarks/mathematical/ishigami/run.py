"""Compare unit-cube Monte Carlo and LHS integration on Ishigami."""

from __future__ import annotations

import numpy as np
from uqra import LatinHypercubeSampler, MonteCarloSampler


def ishigami(unit_samples: np.ndarray, a: float = 7.0, b: float = 0.1) -> np.ndarray:
    """Evaluate Ishigami after mapping [0, 1]^3 to [-pi, pi]^3."""
    x = 2.0 * np.pi * unit_samples - np.pi
    return (
        np.sin(x[:, 0]) + a * np.sin(x[:, 1]) ** 2 + b * x[:, 2] ** 4 * np.sin(x[:, 0])
    )


def main() -> None:
    n_samples = 4096
    expected_mean = 3.5
    for sampler in (MonteCarloSampler(3), LatinHypercubeSampler(3)):
        result = sampler.sample(n_samples, random_state=20260731)
        estimate = float(np.mean(ishigami(result.samples)))
        print(
            f"{result.metadata['method']}: mean={estimate:.8f}, error={abs(estimate - expected_mean):.8f}"
        )


if __name__ == "__main__":
    main()
