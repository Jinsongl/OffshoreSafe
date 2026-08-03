"""Issues #090/#091 unified traceability and engineering report tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from offshoresafe import (
    EngineeringAnalysisResult,
    EngineeringReport,
    TraceabilityManifest,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _result(*, context: dict[str, str | None] | None = None) -> EngineeringAnalysisResult:
    return EngineeringAnalysisResult(
        project_id="floating-demo",
        analysis_id="mooring-reliability",
        analysis_type="floating_platform_reliability",
        method="FORM",
        solver_id="openfast-primary",
        adapter="openfast",
        software_version="0.1.0a1.dev0",
        analyzed_at="2026-08-03T12:00:00Z",
        parameters={"limit": 12_000.0, "channel": "mooring_tension"},
        traceability={
            "project_source_file": "project.yaml",
            "solver_input": {
                "source_file": "main.fst",
                "input_file_hash": HASH_A,
                "solver_version": "3.5.3",
            },
            "solver_output": {
                "source_file": "main.out",
                "output_file_hash": HASH_B,
                "solver_version": "3.5.3",
            },
            "context": context or {"case_id": "DLC-1.6", "sample_id": "sample-42"},
        },
        payload={"failure_probability": 1.2e-4, "reliability_index": 3.67},
    )


def test_manifest_normalizes_provenance_and_has_stable_fingerprints() -> None:
    first = TraceabilityManifest.from_result(_result())
    second = TraceabilityManifest.from_result(_result())

    assert first == second
    assert first.input_file_hash == HASH_A
    assert first.output_file_hash == HASH_B
    assert first.solver_version == "3.5.3"
    assert first.validate().complete
    assert all(
        len(value) == 64
        for value in (first.parameters_hash, first.payload_hash, first.result_hash)
    )


def test_manifest_reports_missing_required_and_optional_context() -> None:
    result = _result(context={"case_id": None, "sample_id": None})
    data = result.to_dict()
    data["traceability"]["solver_input"].pop("input_file_hash")

    validation = TraceabilityManifest.from_result(
        EngineeringAnalysisResult.from_dict(data)
    ).validate()

    assert not validation.complete
    assert validation.missing_fields == ("input_file_hash",)
    assert len(validation.warnings) == 2


def test_markdown_and_excel_share_normalized_content(tmp_path: Path) -> None:
    report = EngineeringReport(_result())
    markdown = report.to_markdown(tmp_path / "report.md")
    workbook = report.to_excel(tmp_path / "report.xlsx")

    text = markdown.read_text(encoding="utf-8")
    assert "floating-demo" in text
    assert report.manifest.result_hash in text
    with zipfile.ZipFile(workbook) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        assert {f"xl/worksheets/sheet{i}.xml" for i in range(1, 5)} <= names
        content = "".join(
            archive.read(name).decode("utf-8")
            for name in names
            if name.startswith("xl/worksheets/")
        )
        assert "floating-demo" in content
        assert report.manifest.result_hash in content


def test_report_rejects_wrong_extensions(tmp_path: Path) -> None:
    report = EngineeringReport(_result())
    with pytest.raises(ValueError, match=r"must use \.xlsx"):
        report.to_excel(tmp_path / "report.xls")


def test_pdf_is_reopenable_when_optional_dependency_is_installed(tmp_path: Path) -> None:
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    target = EngineeringReport(_result()).to_pdf(tmp_path / "report.pdf")
    reader = pypdf.PdfReader(target)
    assert len(reader.pages) == 4
    assert "floating-demo" in "".join(page.extract_text() or "" for page in reader.pages)
