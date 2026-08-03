"""Descriptive statistics for normalized solver channels."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from offshoresafe.solver import SolverResult


@dataclass(frozen=True, slots=True)
class ChannelStatistics:
    """Scalar descriptive statistics for one result channel."""

    count: int
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float
    rms: float
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class StatisticsResult:
    """Immutable collection of per-channel statistics and traceability data."""

    channels: Mapping[str, ChannelStatistics]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.channels:
            raise ValueError("statistics channels must not be empty")
        object.__setattr__(self, "channels", MappingProxyType(dict(self.channels)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def __getitem__(self, channel: str) -> ChannelStatistics:
        return self.channels[channel]

    @property
    def channel_names(self) -> tuple[str, ...]:
        """Analyzed channel names in source or requested order."""

        return tuple(self.channels)


def compute_statistics(
    result: SolverResult,
    channels: Iterable[str] | None = None,
    *,
    ddof: int = 0,
) -> StatisticsResult:
    """Compute deterministic descriptive statistics for solver channels.

    ``ddof=0`` computes population standard deviation; ``ddof=1`` computes the
    usual sample standard deviation. More general non-negative integer values
    are accepted when fewer than the channel sample count.
    """

    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError("ddof must be a non-negative integer")

    selected = result.channel_names if channels is None else tuple(channels)
    if not selected:
        raise ValueError("at least one channel must be selected")
    if len(set(selected)) != len(selected):
        raise ValueError("selected channel names must be unique")
    unknown = [name for name in selected if name not in result.channels]
    if unknown:
        raise KeyError(f"unknown solver channels: {', '.join(unknown)}")

    statistics: dict[str, ChannelStatistics] = {}
    for name in selected:
        values = result.channels[name]
        count = len(values)
        if ddof >= count:
            raise ValueError(f"ddof must be smaller than channel sample count {count}")
        mean = math.fsum(values) / count
        variance = math.fsum((value - mean) ** 2 for value in values) / (count - ddof)
        statistics[name] = ChannelStatistics(
            count=count,
            mean=mean,
            standard_deviation=math.sqrt(max(variance, 0.0)),
            minimum=min(values),
            maximum=max(values),
            rms=math.sqrt(math.fsum(value * value for value in values) / count),
            unit=result.units.get(name),
        )

    metadata = dict(result.metadata)
    metadata.update(
        {
            "processing_method": "channel_statistics",
            "ddof": ddof,
            "sample_count": result.sample_count,
        }
    )
    return StatisticsResult(channels=statistics, metadata=metadata)
