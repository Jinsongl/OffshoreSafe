"""Generate certification-style reports for the three structural vertical cases."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages/offshoresafe/src"),
    str(ROOT / "packages/uqra/src"),
]

from offshoresafe import (  # noqa: E402
    AssessmentCriteria,
    EngineeringAnalysisWorkflow,
    EngineeringReport,
    OffshoreProject,
    ReportTemplate,
)

OUTPUT = ROOT / "output"
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
CASES = (
    ("tower", "tower_reliability", "tower-form", 3.0),
    ("blade", "blade_fatigue_reliability", "blade-fatigue-form", 1.0),
    ("floating", "floating_reliability", "floating-form", 2.5),
)


def main() -> None:
    template = ReportTemplate(
        version="1.1",
        organization="OffshoreSafe benchmark programme",
        prepared_by="Automated benchmark",
    )
    for name, folder, analysis_id, minimum_beta in CASES:
        project = OffshoreProject.load(
            ROOT / "benchmarks" / "offshore" / folder / "input" / "project.yaml"
        )
        result = EngineeringAnalysisWorkflow(project).run(
            analysis_id,
            analyzed_at=FIXED_TIME,
            case_id=f"{name}-reference",
            sample_id="sample-001",
        )
        report = EngineeringReport(
            result,
            title=f"OffshoreSafe {name.title()} Reliability Report",
            template=template,
            criteria=AssessmentCriteria(
                reference=f"{name.title()} benchmark acceptance basis",
                minimum_reliability_index=minimum_beta,
            ),
        )
        if report.assessment.status != "PASS":
            raise RuntimeError(f"{name} report acceptance failed")
        if not report.manifest.validate().complete:
            raise RuntimeError(f"{name} traceability manifest is incomplete")
        if not report.manifest.verify_files().verified:
            raise RuntimeError(f"{name} source-file audit failed")
        artifacts = {
            "markdown": report.to_markdown(OUTPUT / "reports" / f"{name}.md"),
            "excel": report.to_excel(OUTPUT / "spreadsheets" / f"{name}.xlsx"),
            "pdf": report.to_pdf(OUTPUT / "pdf" / f"{name}.pdf"),
            "manifest": report.manifest.export(
                OUTPUT / "manifests" / f"{name}.manifest.json"
            ),
        }
        print(f"{name}: " + ", ".join(str(path) for path in artifacts.values()))


if __name__ == "__main__":
    main()
