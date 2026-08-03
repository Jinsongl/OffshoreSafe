"""Deterministic Issue #070 tower reliability benchmark."""

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
    result = workflow.run("tower-form", analyzed_at=FIXED_TIME)
    payload = result.payload

    mean_margin = 355.0 * 0.1 * 1000.0 - 25_000.0
    linearized_std = math.sqrt(
        (0.1 * 1000.0 * 17.75) ** 2
        + (355.0 * 1000.0 * 0.005) ** 2
        + (25_000.0 * 0.05) ** 2
    )
    first_order_beta = mean_margin / linearized_std

    assert payload["reference_moment"] == 25_000.0
    assert payload["converged"] is True
    assert math.isclose(payload["beta"], 3.935486410901823, rel_tol=1.0e-10)
    assert abs(payload["beta"] - first_order_beta) / first_order_beta < 0.06
    assert payload["reliability_metadata"]["backend"] == "native"
    assert result.traceability["solver_input"]["input_file_hash"]
    assert result.traceability["solver_output"]["output_file_hash"]
    print("tower reliability benchmark passed")


if __name__ == "__main__":
    main()
