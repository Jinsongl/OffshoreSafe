"""Deterministic Issue #064 engineering workflow benchmark."""

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[3]
for source in (
    ROOT / "packages" / "uqra" / "src",
    ROOT / "packages" / "offshoresafe" / "src",
):
    sys.path.insert(0, str(source))

from offshoresafe import (  # noqa: E402
    EngineeringAnalysisWorkflow,
    OffshoreProject,
)

PROJECT = Path(__file__).parent / "input" / "project.yaml"
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def main() -> None:
    workflow = EngineeringAnalysisWorkflow(OffshoreProject.load(PROJECT))
    statistics = workflow.run("statistics", analyzed_at=FIXED_TIME)
    extreme = workflow.run("extreme", analyzed_at=FIXED_TIME)
    fatigue = workflow.run("fatigue", analyzed_at=FIXED_TIME)

    channel = statistics.payload["channels"]["tower_base_fore_aft_moment"]
    assert math.isclose(channel["mean"], 45.0 / 7.0, rel_tol=1.0e-12)
    assert channel["maximum"] == 20.0
    assert extreme.payload["sample_count"] == 3
    assert math.isclose(
        extreme.payload["return_period_response"], 35.897703179724914, rel_tol=1.0e-12
    )
    assert math.isclose(fatigue.payload["damage"], 1.2375e-11, rel_tol=1.0e-12)
    assert math.isclose(
        fatigue.payload["damage_equivalent_load"],
        4.983277467062981,
        rel_tol=1.0e-12,
    )
    assert statistics.traceability["solver_input"]["input_file_hash"]
    assert statistics.traceability["solver_output"]["output_file_hash"]
    print("engineering analysis workflow benchmark passed")


if __name__ == "__main__":
    main()
