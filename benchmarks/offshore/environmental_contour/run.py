"""Deterministic Issues #080/#081 Hs-Tp IFORM benchmark."""

from __future__ import annotations

import hashlib
import math
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import yaml
from scipy import stats

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import (  # noqa: E402
    AssessmentCriteria,
    EngineeringAnalysisResult,
    EngineeringReport,
    MetoceanModel,
    ReportTemplate,
)

INPUT = Path(__file__).with_name("input.yaml")
EXPECTED = Path(__file__).with_name("expected_result.yaml")
OUTPUT = ROOT / "output"
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config = yaml.safe_load(INPUT.read_text(encoding="utf-8"))
    expected = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    model = MetoceanModel.from_config(
        {
            "variables": config["variables"],
            "correlation_matrix": config["correlation_matrix"],
        }
    )
    return_period = float(config["return_period_years"])
    events_per_period = float(config["events_per_period"])
    contour = model.iform_contour(
        return_period,
        events_per_period=events_per_period,
        n_points=int(config["n_points"]),
    )
    expected_probability = float(expected["failure_probability"])
    expected_beta = float(expected["reliability_index"])
    tolerance = float(expected["tolerances"]["relative"])

    assert math.isclose(
        expected_beta,
        stats.norm.ppf(1.0 - expected_probability),
        rel_tol=tolerance,
    )
    assert math.isclose(contour.beta, expected_beta, rel_tol=tolerance)
    assert np.allclose(
        np.linalg.norm(contour.standard_normal_points, axis=1), expected_beta
    )
    assert np.all(np.asarray(contour.points) > 0.0)
    assert np.allclose(
        contour.points[0],
        [
            expected["first_point"]["significant_wave_height"],
            expected["first_point"]["peak_period"],
        ],
        rtol=tolerance,
    )
    assert contour.variable_names == ("significant_wave_height", "peak_period")

    from offshoresafe import __version__ as offshoresafe_version
    from uqra import __version__ as uqra_version

    result = EngineeringAnalysisResult(
        project_id=str(config["project_id"]),
        analysis_id="hs-tp-iform-50-year",
        analysis_type="environmental_contour",
        method="IFORM",
        solver_id="metocean-reference",
        adapter="offshoresafe-metocean",
        software_version=offshoresafe_version,
        analyzed_at=FIXED_TIME.isoformat().replace("+00:00", "Z"),
        parameters={
            "return_period_years": return_period,
            "events_per_period": events_per_period,
            "n_points": config["n_points"],
            "variables": config["variables"],
            "correlation_matrix": config["correlation_matrix"],
        },
        traceability={
            "project_source_file": str(INPUT.resolve()),
            "project_source_file_hash": _hash(INPUT),
            "solver_input": {
                "source_file": str(INPUT.resolve()),
                "input_file_hash": _hash(INPUT),
            },
            "solver_output": {
                "source_file": str(EXPECTED.resolve()),
                "output_file_hash": _hash(EXPECTED),
            },
            "context": {
                "case_id": "environmental-contour-reference",
                "sample_id": "deterministic-contour",
            },
            "runtime": {
                "algorithm_backend": "native",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "uqra_version": uqra_version,
            },
        },
        payload={
            "pf": expected_probability,
            "beta": contour.beta,
            "variable_names": contour.variable_names,
            "units": contour.units,
            "points": contour.points,
        },
    )
    report = EngineeringReport(
        result,
        title="OffshoreSafe Environmental Contour Report",
        template=ReportTemplate(
            version="1.1",
            organization="OffshoreSafe benchmark programme",
            prepared_by="Automated benchmark",
        ),
        criteria=AssessmentCriteria(
            reference="50-year daily-event IFORM benchmark acceptance basis",
            minimum_reliability_index=expected_beta,
        ),
    )
    if report.assessment.status != "PASS":
        raise RuntimeError("environmental contour report acceptance failed")
    if not report.manifest.validate().complete:
        raise RuntimeError("environmental contour traceability is incomplete")
    if not report.manifest.verify_files().verified:
        raise RuntimeError("environmental contour source-file audit failed")
    artifacts = {
        "markdown": report.to_markdown(OUTPUT / "reports" / "environmental.md"),
        "excel": report.to_excel(OUTPUT / "spreadsheets" / "environmental.xlsx"),
        "pdf": report.to_pdf(OUTPUT / "pdf" / "environmental.pdf"),
        "manifest": report.manifest.export(
            OUTPUT / "manifests" / "environmental.manifest.json"
        ),
    }
    print(
        "Hs-Tp IFORM environmental contour benchmark passed: "
        + ", ".join(str(path) for path in artifacts.values())
    )


if __name__ == "__main__":
    main()
