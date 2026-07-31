"""Unit and statistical validation tests for UQRA sampling engines."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import qmc
from uqra import (
    LatinHypercubeSampler,
    LHSSampler,
    MonteCarloSampler,
    SamplingResult,
    SobolSampler,
)


@pytest.mark.parametrize(
    "sampler", [MonteCarloSampler(3), LatinHypercubeSampler(3), SobolSampler(3)]
)
def test_sampling_result_shape_range_and_metadata(sampler: object) -> None:
    result = sampler.sample(16, random_state=42)  # type: ignore[attr-defined]
    assert isinstance(result, SamplingResult)
    assert result.samples.shape == (16, 3)
    assert np.all((result.samples >= 0.0) & (result.samples < 1.0))
    assert result.metadata["n_samples"] == 16
    assert result.metadata["dimension"] == 3
    assert "method" in result.metadata


@pytest.mark.parametrize(
    "sampler", [MonteCarloSampler(2), LatinHypercubeSampler(2), SobolSampler(2)]
)
def test_sampling_is_reproducible(sampler: object) -> None:
    first = sampler.sample(16, random_state=7)  # type: ignore[attr-defined]
    second = sampler.sample(16, random_state=7)  # type: ignore[attr-defined]
    assert first.samples == pytest.approx(second.samples)


def test_monte_carlo_statistical_convergence() -> None:
    samples = MonteCarloSampler(2).sample(100_000, random_state=20260731).samples
    assert np.mean(samples, axis=0) == pytest.approx([0.5, 0.5], abs=0.003)
    assert np.var(samples, axis=0) == pytest.approx([1.0 / 12.0] * 2, abs=0.001)
    assert np.corrcoef(samples, rowvar=False)[0, 1] == pytest.approx(0.0, abs=0.01)


def test_latin_hypercube_uses_each_stratum_once() -> None:
    n_samples = 32
    samples = LatinHypercubeSampler(4).sample(n_samples, random_state=11).samples
    strata = np.floor(samples * n_samples).astype(int)
    for column in strata.T:
        assert np.sort(column).tolist() == list(range(n_samples))
    assert LHSSampler is LatinHypercubeSampler


def test_sobol_has_lower_discrepancy_than_seeded_monte_carlo() -> None:
    sobol = SobolSampler(3).sample(256, random_state=9)
    monte_carlo = MonteCarloSampler(3).sample(256, random_state=9)
    assert qmc.discrepancy(sobol.samples) < qmc.discrepancy(monte_carlo.samples)
    assert sobol.metadata["balance_guaranteed"] is True


def test_sobol_marks_non_power_of_two_balance_limitation() -> None:
    with pytest.warns(UserWarning, match="power of 2"):
        result = SobolSampler(2).sample(10, random_state=1)
    assert result.metadata["balance_guaranteed"] is False


def test_sampling_result_is_immutable() -> None:
    result = MonteCarloSampler(1).sample(2, random_state=0)
    with pytest.raises(ValueError):
        result.samples[0, 0] = 1.0
    with pytest.raises(TypeError):
        result.metadata["method"] = "changed"  # type: ignore[index]


@pytest.mark.parametrize("dimension", [0, -1])
def test_sampler_requires_positive_dimension(dimension: int) -> None:
    with pytest.raises(ValueError, match="dimension must be positive"):
        MonteCarloSampler(dimension)


@pytest.mark.parametrize("n_samples", [0, -1])
def test_sampler_requires_positive_sample_count(n_samples: int) -> None:
    with pytest.raises(ValueError, match="n_samples must be positive"):
        MonteCarloSampler(1).sample(n_samples)
