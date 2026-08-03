"""Generate Issue #090/#091 traceability and report artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from offshoresafe import EngineeringAnalysisWorkflow, EngineeringReport, OffshoreProject

ROOT = Path(__file__).parents[3]
CASE = ROOT / "benchmarks" / "offshore" / "engineering_workflow"
OUTPUT = ROOT / "output"


def main() -> None:
    project = OffshoreProject.load(CASE / "input" / "project.yaml")
    result = EngineeringAnalysisWorkflow(project).run(
        "extreme",
        analyzed_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        case_id="benchmark-case",
        sample_id="sample-001",
    )
    report = EngineeringReport(result, title="OffshoreSafe Engineering Benchmark")
    if not report.manifest.validate().complete:
        raise RuntimeError("traceability manifest is incomplete")
    artifacts = {
        "markdown": report.to_markdown(OUTPUT / "reports" / "engineering-report.md"),
        "excel": report.to_excel(OUTPUT / "spreadsheets" / "engineering-report.xlsx"),
        "pdf": report.to_pdf(OUTPUT / "pdf" / "engineering-report.pdf"),
    }
    for name, path in artifacts.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
