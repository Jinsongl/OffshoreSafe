"""Normalized solver result contracts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from types import MappingProxyType
from typing import Any


def _float_tuple(values: Sequence[float], *, label: str) -> tuple[float, ...]:
    converted = tuple(float(value) for value in values)
    if not converted:
        raise ValueError(f"{label} must not be empty")
    if not all(math.isfinite(value) for value in converted):
        raise ValueError(f"{label} must contain only finite values")
    return converted


@dataclass(frozen=True, slots=True)
class SolverResult:
    """Immutable, solver-independent time-series result.

    Channel names are canonical OffshoreSafe names after adapter mapping. Values
    and time are copied into tuples so a result cannot change when a parser reuses
    its input buffers.
    """

    time: Sequence[float]
    channels: Mapping[str, Sequence[float]]
    units: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        time = _float_tuple(self.time, label="time")
        if any(current <= previous for previous, current in pairwise(time)):
            raise ValueError("time must be strictly increasing")

        channels: dict[str, tuple[float, ...]] = {}
        for name, values in self.channels.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("channel names must be non-empty strings")
            values_tuple = _float_tuple(values, label=f"channel {name!r}")
            if len(values_tuple) != len(time):
                raise ValueError(
                    f"channel {name!r} has {len(values_tuple)} values; "
                    f"expected {len(time)}"
                )
            channels[name] = values_tuple
        if not channels:
            raise ValueError("channels must not be empty")

        units = dict(self.units)
        unknown_units = units.keys() - channels.keys()
        if unknown_units:
            names = ", ".join(sorted(unknown_units))
            raise ValueError(f"units reference unknown channels: {names}")
        if not all(isinstance(unit, str) for unit in units.values()):
            raise ValueError("units must be strings")

        object.__setattr__(self, "time", time)
        object.__setattr__(self, "channels", MappingProxyType(channels))
        object.__setattr__(self, "units", MappingProxyType(units))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def sample_count(self) -> int:
        """Number of time samples."""

        return len(self.time)

    @property
    def channel_names(self) -> tuple[str, ...]:
        """Canonical channel names in parser order."""

        return tuple(self.channels)
