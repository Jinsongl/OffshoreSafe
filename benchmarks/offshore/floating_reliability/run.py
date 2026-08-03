"""Deterministic Issue #072 floating response reliability benchmark."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages/offshoresafe/src"),
    str(ROOT / "packages/uqra/src"),
]

from offshoresafe import SolverResult, analyze_floating_reliability  # noqa: E402


def main() -> None:
    variables = {
        "significant_wave_height": {
            "distribution": "Lognormal",
            "parameters": {"mean": 6.0, "std": 0.5},
        },
        "peak_period": {
            "distribution": "Lognormal",
            "parameters": {"mean": 10.0, "std": 0.6},
        },
        "current_speed": {
            "distribution": "Lognormal",
            "parameters": {"mean": 1.0, "std": 0.1},
        },
        "mooring_stiffness": {
            "distribution": "Lognormal",
            "parameters": {"mean": 1000.0, "std": 80.0},
        },
    }
    settings = {
        "channel": "platform_pitch",
        "response_kind": "platform_motion",
        "response_limit": 7.0,
        "reference_environment": {
            "significant_wave_height": 6.0,
            "peak_period": 10.0,
            "current_speed": 1.0,
            "mooring_stiffness": 1000.0,
        },
        "variables": variables,
    }
    result = SolverResult(
        time=range(5),
        channels={"platform_pitch": [0, 3, -4, 2, 0]},
        units={"platform_pitch": "deg"},
    )
    payload, _ = analyze_floating_reliability(result, settings)
    assert payload["reference_response"] == 4.0
    assert payload["response_limit"] == 7.0
    assert math.isclose(payload["beta"], 2.6129892715077685, rel_tol=1.0e-10)
    assert math.isclose(payload["pf"], 0.0044877059832518175, rel_tol=1.0e-10)
    assert payload["converged"] is True
    print("floating-platform reliability benchmark passed")


if __name__ == "__main__":
    main()
