"""Deterministic Issue #072 floating response reliability benchmark."""

from __future__ import annotations

import math
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages/offshoresafe/src"),
    str(ROOT / "packages/uqra/src"),
]

from offshoresafe import (  # noqa: E402
    EngineeringAnalysisWorkflow,
    OffshoreProject,
)


def main() -> None:
    project = OffshoreProject.load(Path(__file__).parent / "input" / "project.yaml")
    result = EngineeringAnalysisWorkflow(project).run(
        "floating-form",
        analyzed_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        case_id="floating-reference",
        sample_id="sample-001",
    )
    payload = result.payload
    assert payload["reference_response"] == 4.0
    assert payload["response_limit"] == 7.0
    assert math.isclose(payload["beta"], 2.6129892715077685, rel_tol=1.0e-10)
    assert math.isclose(payload["pf"], 0.0044877059832518175, rel_tol=1.0e-10)
    assert payload["converged"] is True
    assert result.traceability["runtime"]["algorithm_backend"] == "native"
    print("floating-platform reliability benchmark passed")


if __name__ == "__main__":
    main()
