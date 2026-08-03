"""Issues #062 and #063 rainflow and fatigue tests."""

from __future__ import annotations

import math

import pytest
from offshoresafe import (
    RainflowCycle,
    SNCurve,
    calculate_del,
    calculate_fatigue_damage,
    count_rainflow,
)


def test_rainflow_counts_constant_amplitude_history() -> None:
    result = count_rainflow([0, 10, 0, 10, 0])

    assert sum(cycle.count for cycle in result.cycles) == 2.0
    assert all(cycle.range == 10.0 for cycle in result.cycles)
    assert all(cycle.mean == 5.0 for cycle in result.cycles)
    assert result.metadata["processing_method"] == "rainflow_counting"


def test_rainflow_removes_repeated_non_reversal_points() -> None:
    result = count_rainflow([0, 0, 2, 4, 4, 2, 0])

    assert sum(cycle.count for cycle in result.cycles) == 1.0
    assert all(cycle.range == 4.0 and cycle.mean == 2.0 for cycle in result.cycles)


def test_miner_damage_matches_power_law_sn_curve() -> None:
    cycles = [RainflowCycle(10.0, 0.0, 2.0), RainflowCycle(20.0, 0.0, 1.0)]
    curve = SNCurve(slope=3.0, log10_intercept=6.0)
    result = calculate_fatigue_damage(cycles, curve)

    expected = 2.0 / 1000.0 + 1.0 / 125.0
    assert result.damage == pytest.approx(expected)
    assert math.fsum(result.contributions) == result.damage


def test_endurance_limit_excludes_low_ranges() -> None:
    curve = SNCurve(slope=3.0, log10_intercept=6.0, endurance_limit=5.0)
    result = calculate_fatigue_damage([RainflowCycle(5.0, 0.0, 100.0)], curve)
    assert result.damage == 0.0


def test_del_matches_equivalent_damage_definition() -> None:
    cycles = [RainflowCycle(10.0, 0.0, 2.0), RainflowCycle(20.0, 0.0, 1.0)]
    expected = ((2 * 10**3 + 20**3) / 100.0) ** (1 / 3)
    assert calculate_del(cycles, slope=3.0, equivalent_cycles=100.0) == pytest.approx(
        expected
    )


@pytest.mark.parametrize("series", [[], [1.0], [0.0, math.nan]])
def test_invalid_rainflow_series_is_rejected(series: list[float]) -> None:
    with pytest.raises(ValueError, match="at least two finite"):
        count_rainflow(series)


def test_invalid_fatigue_parameters_are_rejected() -> None:
    with pytest.raises(ValueError, match="slope"):
        SNCurve(slope=0.0, log10_intercept=10.0)
    with pytest.raises(ValueError, match="equivalent_cycles"):
        calculate_del([], slope=3.0, equivalent_cycles=0.0)
