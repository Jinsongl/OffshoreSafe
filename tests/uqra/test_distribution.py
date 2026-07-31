"""Unit tests for the UQRA distribution interface."""

from __future__ import annotations

import numpy as np
import pytest
from uqra import Distribution, Lognormal, Normal, Uniform, Weibull


@pytest.mark.parametrize(
    "distribution",
    [
        Normal(mean=2.0, std=3.0),
        Lognormal(mean=2.0, std=0.5),
        Weibull(scale=4.0, shape=2.0),
        Uniform(lower=-1.0, upper=3.0),
    ],
)
def test_distributions_implement_common_interface(distribution: Distribution) -> None:
    assert isinstance(distribution.pdf(1.0), np.floating)
    assert isinstance(distribution.cdf(1.0), np.floating)
    assert isinstance(distribution.ppf(0.5), np.floating)
    assert distribution.sample(size=3, random_state=42).shape == (3,)


def test_normal_matches_reference_values() -> None:
    distribution = Normal(mean=0.0, std=1.0)

    assert distribution.pdf(0.0) == pytest.approx(1.0 / np.sqrt(2.0 * np.pi))
    assert distribution.cdf(0.0) == pytest.approx(0.5)
    assert distribution.ppf(0.975) == pytest.approx(1.959963984540054)


def test_lognormal_uses_arithmetic_moments() -> None:
    distribution = Lognormal(mean=10.0, std=2.0)
    samples = distribution.sample(size=200_000, random_state=1234)

    assert np.mean(samples) == pytest.approx(10.0, rel=0.003)
    assert np.std(samples) == pytest.approx(2.0, rel=0.01)
    assert np.all(samples > 0.0)


def test_weibull_cdf_and_ppf_are_inverses() -> None:
    distribution = Weibull(scale=10.5, shape=2.1)
    probabilities = np.array([0.1, 0.5, 0.9])

    assert distribution.cdf(distribution.ppf(probabilities)) == pytest.approx(
        probabilities
    )


def test_uniform_reference_values() -> None:
    distribution = Uniform(lower=2.0, upper=6.0)

    assert distribution.pdf(4.0) == pytest.approx(0.25)
    assert distribution.cdf(4.0) == pytest.approx(0.5)
    assert distribution.ppf(0.75) == pytest.approx(5.0)


def test_sampling_is_reproducible() -> None:
    distribution = Normal()

    assert distribution.sample(5, 17) == pytest.approx(distribution.sample(5, 17))


@pytest.mark.parametrize("probability", [-0.1, 1.1])
def test_ppf_rejects_invalid_probability(probability: float) -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        Normal().ppf(probability)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: Normal(std=0.0), "std must be positive"),
        (lambda: Lognormal(mean=0.0, std=1.0), "mean must be positive"),
        (lambda: Weibull(scale=1.0, shape=0.0), "shape must be positive"),
        (lambda: Uniform(lower=1.0, upper=1.0), "upper must be greater"),
    ],
)
def test_invalid_distribution_parameters_are_rejected(
    factory: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()  # type: ignore[operator]
