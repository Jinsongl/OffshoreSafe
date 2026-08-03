"""Rainflow cycle counting and fatigue calculations."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True, slots=True)
class RainflowCycle:
    """A counted stress/load cycle."""

    range: float
    mean: float
    count: float


@dataclass(frozen=True, slots=True)
class RainflowResult:
    """Immutable rainflow count result."""

    cycles: tuple[RainflowCycle, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cycles", tuple(self.cycles))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class SNCurve:
    """Power-law S-N curve ``N = 10**log10_intercept / range**slope``."""

    slope: float
    log10_intercept: float
    endurance_limit: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.slope) or self.slope <= 0.0:
            raise ValueError("S-N slope must be finite and positive")
        if not math.isfinite(self.log10_intercept):
            raise ValueError("S-N intercept must be finite")
        if self.endurance_limit is not None and (
            not math.isfinite(self.endurance_limit) or self.endurance_limit < 0.0
        ):
            raise ValueError("endurance_limit must be finite and non-negative")

    def cycles_to_failure(self, load_range: float) -> float:
        if not math.isfinite(load_range) or load_range < 0.0:
            raise ValueError("load range must be finite and non-negative")
        if load_range == 0.0 or (
            self.endurance_limit is not None and load_range <= self.endurance_limit
        ):
            return math.inf
        return 10.0**self.log10_intercept / load_range**self.slope


@dataclass(frozen=True, slots=True)
class FatigueDamageResult:
    """Miner damage result with cycle-level contributions."""

    damage: float
    contributions: tuple[float, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "contributions", tuple(self.contributions))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


def _reversals(series: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(value) for value in series)
    if len(values) < 2 or not all(math.isfinite(value) for value in values):
        raise ValueError("series must contain at least two finite values")
    distinct = [values[0]]
    distinct.extend(value for value in values[1:] if value != distinct[-1])
    if len(distinct) < 2:
        return tuple(distinct)
    points = [distinct[0]]
    for left, center, right in zip(distinct, distinct[1:], distinct[2:], strict=False):
        if (center - left) * (right - center) <= 0.0:
            points.append(center)
    points.append(distinct[-1])
    return tuple(points)


def count_rainflow(series: Sequence[float]) -> RainflowResult:
    """Count cycles using the ASTM E1049 four-point rainflow procedure."""

    reversals = _reversals(series)
    if len(reversals) < 2:
        return RainflowResult((), {"processing_method": "rainflow_counting"})
    stack: list[float] = []
    cycles: list[RainflowCycle] = []
    for reversal in reversals:
        stack.append(reversal)
        while len(stack) >= 3:
            older_range = abs(stack[-2] - stack[-3])
            newer_range = abs(stack[-1] - stack[-2])
            if newer_range < older_range:
                break
            mean = (stack[-3] + stack[-2]) / 2.0
            if len(stack) == 3:
                cycles.append(RainflowCycle(older_range, mean, 0.5))
                stack.pop(0)
            else:
                cycles.append(RainflowCycle(older_range, mean, 1.0))
                del stack[-3:-1]
    cycles.extend(
        RainflowCycle(abs(right - left), (left + right) / 2.0, 0.5)
        for left, right in pairwise(stack)
    )
    return RainflowResult(
        tuple(cycles),
        {
            "processing_method": "rainflow_counting",
            "reversal_count": len(reversals),
        },
    )


def calculate_fatigue_damage(
    cycles: RainflowResult | Iterable[RainflowCycle],
    sn_curve: SNCurve,
) -> FatigueDamageResult:
    """Calculate cumulative fatigue damage with Miner's linear rule."""

    cycle_values = (
        cycles.cycles if isinstance(cycles, RainflowResult) else tuple(cycles)
    )
    contributions = tuple(
        cycle.count / sn_curve.cycles_to_failure(cycle.range) for cycle in cycle_values
    )
    return FatigueDamageResult(
        math.fsum(contributions),
        contributions,
        {"processing_method": "miner_damage", "cycle_count": len(cycle_values)},
    )


def calculate_del(
    cycles: RainflowResult | Iterable[RainflowCycle],
    *,
    slope: float,
    equivalent_cycles: float,
) -> float:
    """Calculate damage equivalent load for a constant-amplitude cycle count."""

    if not math.isfinite(slope) or slope <= 0.0:
        raise ValueError("slope must be finite and positive")
    if not math.isfinite(equivalent_cycles) or equivalent_cycles <= 0.0:
        raise ValueError("equivalent_cycles must be finite and positive")
    cycle_values = (
        cycles.cycles if isinstance(cycles, RainflowResult) else tuple(cycles)
    )
    damage_sum = math.fsum(cycle.count * cycle.range**slope for cycle in cycle_values)
    return (damage_sum / equivalent_cycles) ** (1.0 / slope)
