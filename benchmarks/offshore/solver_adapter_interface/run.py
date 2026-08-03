"""Compatibility benchmark for the Issue #051 normalized result contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT / "packages" / "offshoresafe" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "uqra" / "src"))

from offshoresafe import SolverResult  # noqa: E402


def main() -> None:
    count = 10_001
    time = [index * 0.05 for index in range(count)]
    result = SolverResult(
        time=time,
        channels={
            "tower_base_moment": [2.0 * value for value in time],
            "rotor_speed": [8.0 + 0.01 * value for value in time],
        },
        units={"tower_base_moment": "kN m", "rotor_speed": "rpm"},
        metadata={"adapter": "contract-benchmark"},
    )

    assert result.sample_count == count
    assert result.channel_names == ("tower_base_moment", "rotor_speed")
    assert result.channels["tower_base_moment"][-1] == 1_000.0
    print(
        "solver adapter interface benchmark passed: "
        f"{result.sample_count} samples, {len(result.channels)} channels"
    )


if __name__ == "__main__":
    main()
