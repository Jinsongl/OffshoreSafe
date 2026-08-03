"""Peak extraction and extreme-value response calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

from scipy import stats

from offshoresafe.solver import SolverResult


@dataclass(frozen=True, slots=True)
class Peak:
    """One peak extracted from a normalized time-series channel."""

    index: int
    time: float
    value: float


@dataclass(frozen=True, slots=True)
class PeakResult:
    """Immutable peak sequence with source traceability."""

    channel: str
    peaks: tuple[Peak, ...]
    unit: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.channel.strip():
            raise ValueError("channel must be a non-empty string")
        if not self.peaks:
            raise ValueError("peak extraction produced no peaks")
        object.__setattr__(self, "peaks", tuple(self.peaks))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def values(self) -> tuple[float, ...]:
        return tuple(peak.value for peak in self.peaks)


@dataclass(frozen=True, slots=True)
class ExtremeValueFit:
    """Fitted extreme-value distribution."""

    distribution: Literal["gumbel", "weibull"]
    parameters: Mapping[str, float]
    sample_count: int
    unit: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sample_count < 2:
            raise ValueError("at least two extremes are required")
        object.__setattr__(self, "parameters", MappingProxyType(dict(self.parameters)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def quantile(self, probability: float) -> float:
        """Evaluate the fitted distribution quantile."""

        if not 0.0 < probability < 1.0:
            raise ValueError("probability must be strictly between zero and one")
        if self.distribution == "gumbel":
            return float(stats.gumbel_r.ppf(probability, **self.parameters))
        return float(stats.weibull_min.ppf(probability, **self.parameters))


def extract_peaks(
    result: SolverResult,
    channel: str,
    *,
    direction: Literal["maxima", "minima", "absolute"] = "maxima",
    threshold: float | None = None,
    min_distance: int = 1,
) -> PeakResult:
    """Extract local peaks, optionally applying magnitude and spacing filters."""

    if channel not in result.channels:
        raise KeyError(f"unknown solver channel: {channel}")
    if direction not in {"maxima", "minima", "absolute"}:
        raise ValueError("direction must be 'maxima', 'minima', or 'absolute'")
    if (
        isinstance(min_distance, bool)
        or not isinstance(min_distance, int)
        or min_distance < 1
    ):
        raise ValueError("min_distance must be a positive integer")

    values = result.channels[channel]
    transformed = {
        "maxima": values,
        "minima": tuple(-value for value in values),
        "absolute": tuple(abs(value) for value in values),
    }[direction]
    candidates = [
        index
        for index in range(1, len(values) - 1)
        if transformed[index] > transformed[index - 1]
        and transformed[index] >= transformed[index + 1]
        and (threshold is None or transformed[index] >= threshold)
    ]

    # Retain the strongest peak in each exclusion neighbourhood.
    selected: list[int] = []
    for index in sorted(candidates, key=lambda item: transformed[item], reverse=True):
        if all(abs(index - retained) >= min_distance for retained in selected):
            selected.append(index)
    selected.sort()
    peaks = tuple(Peak(index, result.time[index], values[index]) for index in selected)
    metadata = dict(result.metadata)
    metadata.update(
        {
            "processing_method": "peak_extraction",
            "direction": direction,
            "threshold": threshold,
            "min_distance": min_distance,
        }
    )
    return PeakResult(channel, peaks, result.units.get(channel), metadata)


def fit_extreme_distribution(
    extremes: PeakResult | Iterable[float],
    *,
    distribution: Literal["gumbel", "weibull"] = "gumbel",
) -> ExtremeValueFit:
    """Fit a Gumbel-maximum or two-parameter Weibull distribution by MLE."""

    if isinstance(extremes, PeakResult):
        values = extremes.values
        unit = extremes.unit
        metadata = dict(extremes.metadata)
    else:
        values = tuple(float(value) for value in extremes)
        unit = None
        metadata = {}
    if len(values) < 2 or not all(math.isfinite(value) for value in values):
        raise ValueError("extremes must contain at least two finite values")
    if distribution == "gumbel":
        location, scale = stats.gumbel_r.fit(values)
        parameters = {"loc": float(location), "scale": float(scale)}
    elif distribution == "weibull":
        if any(value <= 0.0 for value in values):
            raise ValueError("Weibull extremes must be strictly positive")
        shape, location, scale = stats.weibull_min.fit(values, floc=0.0)
        parameters = {
            "c": float(shape),
            "loc": float(location),
            "scale": float(scale),
        }
    else:
        raise ValueError("distribution must be 'gumbel' or 'weibull'")
    metadata["processing_method"] = "extreme_distribution_fit"
    return ExtremeValueFit(distribution, parameters, len(values), unit, metadata)


def return_period_response(
    fitted: ExtremeValueFit,
    return_period: float,
    *,
    events_per_period: float = 1.0,
) -> float:
    """Return the response exceeded once per requested return period on average."""

    if not math.isfinite(return_period) or return_period <= 1.0:
        raise ValueError("return_period must be finite and greater than one")
    if not math.isfinite(events_per_period) or events_per_period <= 0.0:
        raise ValueError("events_per_period must be finite and positive")
    probability = 1.0 - 1.0 / (return_period * events_per_period)
    return fitted.quantile(probability)
