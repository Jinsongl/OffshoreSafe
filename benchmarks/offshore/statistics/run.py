"""Deterministic Issue #060 channel statistics benchmark."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import SolverResult, compute_statistics  # noqa: E402


def main() -> None:
    case = Path(__file__).parent
    expected = yaml.safe_load(
        (case / "expected_result.yaml").read_text(encoding="utf-8")
    )
    source = SolverResult(
        time=[0, 1, 2, 3, 4],
        channels={"load": [1, 2, 3, 4, 5]},
        units={"load": "kN"},
        metadata={"adapter": "benchmark"},
    )
    stats = compute_statistics(source)[expected["channel"]]

    assert stats.count == expected["sample_count"]
    assert math.isclose(stats.mean, expected["mean"], abs_tol=1e-14)
    assert math.isclose(
        stats.standard_deviation,
        expected["standard_deviation"],
        abs_tol=1e-14,
    )
    assert stats.minimum == expected["minimum"]
    assert stats.maximum == expected["maximum"]
    assert math.isclose(stats.rms, expected["rms"], abs_tol=1e-14)
    print("statistics benchmark passed: analytical five-point sequence")


if __name__ == "__main__":
    main()
