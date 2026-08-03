"""Deterministic Issue #071 blade fatigue reliability benchmark."""

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import (  # noqa: E402
    EngineeringAnalysisWorkflow,
    OffshoreProject,
)

PROJECT = Path(__file__).parent / "input" / "project.yaml"
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def main() -> None:
    workflow = EngineeringAnalysisWorkflow(OffshoreProject.load(PROJECT))
    result = workflow.run("blade-fatigue-form", analyzed_at=FIXED_TIME)
    payload = result.payload

    analytical_damage = 50.0 * 12_375.0 / 10.0**6
    assert math.isclose(payload["reference_damage"], analytical_damage, rel_tol=1.0e-12)
    assert payload["converged"] is True
    assert math.isclose(payload["beta"], 1.214351235599559, rel_tol=1.0e-10)
    assert math.isclose(payload["pf"], 0.11230681416532845, rel_tol=1.0e-10)
    assert payload["reliability_metadata"]["backend"] == "native"
    assert result.traceability["solver_input"]["input_file_hash"]
    assert result.traceability["solver_output"]["output_file_hash"]
    print("blade fatigue reliability benchmark passed")


if __name__ == "__main__":
    main()
