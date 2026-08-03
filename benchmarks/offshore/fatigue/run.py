"""Deterministic Issues #062-#063 fatigue benchmark."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import (  # noqa: E402
    SNCurve,
    calculate_del,
    calculate_fatigue_damage,
    count_rainflow,
)


def main() -> None:
    cycles = count_rainflow([0, 10, 0, 10, 0])
    assert math.fsum(cycle.count for cycle in cycles.cycles) == 2.0
    damage = calculate_fatigue_damage(
        cycles, SNCurve(slope=3.0, log10_intercept=6.0)
    ).damage
    assert math.isclose(damage, 0.002, abs_tol=1e-15)
    assert math.isclose(
        calculate_del(cycles, slope=3.0, equivalent_cycles=2.0),
        10.0,
        abs_tol=1e-14,
    )
    print("rainflow, Miner damage, and DEL benchmark passed")


if __name__ == "__main__":
    main()
