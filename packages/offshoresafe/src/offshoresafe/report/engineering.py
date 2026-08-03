"""Consistent Markdown, Excel, and PDF engineering reports."""

from __future__ import annotations

import json
import zipfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from offshoresafe.analysis.workflow import EngineeringAnalysisResult
from offshoresafe.traceability import TraceabilityManifest


def _display(value: Any) -> str:
    if value is None:
        return "Not provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple, Mapping)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _flatten(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, Mapping):
        for key in sorted(value):
            name = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten(value[key], name))
    elif isinstance(value, (list, tuple)):
        if len(value) <= 12 and not any(isinstance(v, Mapping) for v in value):
            rows.append((prefix, list(value)))
        else:
            for index, item in enumerate(value):
                rows.extend(_flatten(item, f"{prefix}[{index}]"))
    else:
        rows.append((prefix, value))
    return rows


@dataclass(frozen=True, slots=True)
class ReportTemplate:
    """Versioned certification-facing report identity and sign-off fields."""

    version: str = "1.0"
    name: str = "OffshoreSafe Engineering Assessment"
    organization: str = "Not provided"
    prepared_by: str = "Not signed"
    reviewed_by: str = "Not signed"
    approved_by: str = "Not signed"

    def __post_init__(self) -> None:
        if not self.version.strip() or not self.name.strip():
            raise ValueError("report template version and name must be non-empty")


@dataclass(frozen=True, slots=True)
class AssessmentCriteria:
    """Explicit project acceptance criteria; no implicit code limits are assumed."""

    reference: str
    minimum_reliability_index: float | None = None
    maximum_failure_probability: float | None = None

    def __post_init__(self) -> None:
        if not self.reference.strip():
            raise ValueError("assessment criteria reference must be non-empty")
        if (
            self.maximum_failure_probability is not None
            and not 0.0 <= self.maximum_failure_probability <= 1.0
        ):
            raise ValueError("maximum_failure_probability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class EngineeringCheck:
    """One auditable engineering acceptance check."""

    name: str
    actual: float
    operator: str
    limit: float
    unit: str | None
    passed: bool


@dataclass(frozen=True, slots=True)
class EngineeringAssessment:
    """Report-level conclusion derived only from explicit or result-native limits."""

    status: str
    risk_summary: str
    criteria_reference: str
    checks: tuple[EngineeringCheck, ...]


def _assessment(
    result: EngineeringAnalysisResult,
    criteria: AssessmentCriteria | None,
) -> EngineeringAssessment:
    payload = result.payload
    checks: list[EngineeringCheck] = []
    if (
        criteria
        and criteria.minimum_reliability_index is not None
        and "beta" in payload
    ):
        beta = float(payload["beta"])
        limit = criteria.minimum_reliability_index
        checks.append(
            EngineeringCheck(
                "Reliability index", beta, ">=", limit, None, beta >= limit
            )
        )
    if (
        criteria
        and criteria.maximum_failure_probability is not None
        and "pf" in payload
    ):
        pf = float(payload["pf"])
        limit = criteria.maximum_failure_probability
        checks.append(
            EngineeringCheck("Failure probability", pf, "<=", limit, None, pf <= limit)
        )
    native_pairs = (
        ("Reference fatigue damage", "reference_damage", "damage_limit", None),
        (
            "Reference response",
            "reference_response",
            "response_limit",
            payload.get("channel_unit"),
        ),
    )
    for name, actual_key, limit_key, unit in native_pairs:
        if actual_key in payload and limit_key in payload:
            actual = float(payload[actual_key])
            limit = float(payload[limit_key])
            checks.append(
                EngineeringCheck(name, actual, "<=", limit, unit, actual <= limit)
            )
    reference = criteria.reference if criteria else "Result-native limits only"
    if not checks:
        return EngineeringAssessment(
            "NOT ASSESSED",
            "No explicit acceptance criterion or result-native limit was available.",
            reference,
            (),
        )
    failures = tuple(check for check in checks if not check.passed)
    if failures:
        names = ", ".join(check.name for check in failures)
        return EngineeringAssessment(
            "FAIL",
            f"Acceptance limit exceeded or reliability target not met: {names}.",
            reference,
            tuple(checks),
        )
    return EngineeringAssessment(
        "PASS",
        "All declared acceptance checks are satisfied for this analysis result.",
        reference,
        tuple(checks),
    )


class EngineeringReport:
    """Render a single analysis result through consistent report views."""

    def __init__(
        self,
        result: EngineeringAnalysisResult,
        *,
        title: str | None = None,
        template: ReportTemplate | None = None,
        criteria: AssessmentCriteria | None = None,
    ):
        if not isinstance(result, EngineeringAnalysisResult):
            raise TypeError("result must be an EngineeringAnalysisResult")
        self.result = result
        self.manifest = TraceabilityManifest.from_result(result)
        self.template = template or ReportTemplate()
        self.criteria = criteria
        self.assessment = _assessment(result, criteria)
        self.title = title or f"OffshoreSafe Engineering Report - {result.analysis_id}"

    def _sections(self) -> dict[str, list[tuple[str, Any]]]:
        validation = self.manifest.validate()
        summary = [
            ("Project ID", self.result.project_id),
            ("Analysis ID", self.result.analysis_id),
            ("Template", self.template.name),
            ("Template version", self.template.version),
            ("Organization", self.template.organization),
            ("Analysis type", self.result.analysis_type),
            ("Method", self.result.method),
            ("Solver", self.result.solver_id),
            ("Adapter", self.result.adapter),
            ("Analysis timestamp", self.result.analyzed_at),
            (
                "Traceability status",
                "Complete" if validation.complete else "Incomplete",
            ),
            ("Engineering status", self.assessment.status),
            ("Result SHA-256", self.manifest.result_hash),
        ]
        trace = [
            (key.replace("_", " ").title(), value)
            for key, value in self.manifest.to_dict().items()
            if key != "validation"
        ]
        trace.extend(
            [
                ("Validation complete", validation.complete),
                ("Missing fields", validation.missing_fields),
                ("Invalid fields", validation.invalid_fields),
                ("Warnings", validation.warnings),
            ]
        )
        audit = self.manifest.verify_files()
        trace.append(("Current file audit", "Verified" if audit.verified else "Failed"))
        for check in audit.checks:
            trace.append(
                (
                    f"File audit - {check.role}",
                    "Match" if check.matches else "Mismatch or unavailable",
                )
            )
        assessment = [
            ("Overall status", self.assessment.status),
            ("Criteria reference", self.assessment.criteria_reference),
            ("Risk summary", self.assessment.risk_summary),
        ]
        for check in self.assessment.checks:
            unit = f" {check.unit}" if check.unit else ""
            assessment.append(
                (
                    check.name,
                    f"{_display(check.actual)}{unit} {check.operator} "
                    f"{_display(check.limit)}{unit} - "
                    f"{'PASS' if check.passed else 'FAIL'}",
                )
            )
        return {
            "Summary": summary,
            "Assessment": assessment,
            "Parameters": _flatten(self.result.parameters),
            "Results": _flatten(self.result.payload),
            "Traceability": trace,
            "Approval": [
                ("Prepared by", self.template.prepared_by),
                ("Reviewed by", self.template.reviewed_by),
                ("Approved by", self.template.approved_by),
                ("Report template version", self.template.version),
            ],
        }

    def to_markdown(self, path: str | Path) -> Path:
        """Write a human-readable Markdown engineering report."""

        target = self._target(path, ".md")
        lines = [f"# {self.title}", ""]
        for section, rows in self._sections().items():
            lines.extend([f"## {section}", "", "| Field | Value |", "|---|---|"])
            for key, value in rows:
                safe = _display(value).replace("|", "\\|").replace("\n", "<br>")
                lines.append(f"| {key} | {safe} |")
            lines.append("")
        target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
        return target

    def to_excel(self, path: str | Path) -> Path:
        """Write a dependency-free Office Open XML workbook with four sheets."""

        target = self._target(path, ".xlsx")
        sections = self._sections()
        sheets = list(sections)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as book:
            book.writestr("[Content_Types].xml", _content_types(len(sheets)))
            book.writestr("_rels/.rels", _root_relationships())
            book.writestr("xl/workbook.xml", _workbook(sheets))
            book.writestr(
                "xl/_rels/workbook.xml.rels", _workbook_relationships(len(sheets))
            )
            book.writestr("xl/styles.xml", _styles())
            for index, (name, rows) in enumerate(sections.items(), 1):
                book.writestr(
                    f"xl/worksheets/sheet{index}.xml",
                    _worksheet(self.title, name, rows),
                )
        return target

    def to_pdf(self, path: str | Path) -> Path:
        """Write a paginated PDF; ReportLab is an optional report dependency."""

        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                PageBreak,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError as error:
            raise RuntimeError(
                "PDF export requires the optional 'offshoresafe[reports]' dependency"
            ) from error

        target = self._target(path, ".pdf")
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#12344D"),
            spaceAfter=8 * mm,
        )
        body = styles["BodyText"]
        body.fontSize = 8
        body.leading = 10
        story: list[Any] = [Paragraph(escape(self.title), title_style)]
        for section_index, (section, rows) in enumerate(self._sections().items()):
            if section_index:
                story.append(PageBreak())
            story.append(Paragraph(escape(section), styles["Heading1"]))
            story.append(Spacer(1, 3 * mm))
            table_data = [["Field", "Value"]] + [
                [
                    Paragraph(escape(str(key)), body),
                    Paragraph(escape(_display(value)), body),
                ]
                for key, value in rows
            ]
            table = Table(table_data, colWidths=[55 * mm, 125 * mm], repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B87")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F2F6F8")],
                        ),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#12344D")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(table)
        document = SimpleDocTemplate(
            str(target),
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
            title=self.title,
            author="OffshoreSafe",
        )
        document.build(story)
        return target

    def export_all(
        self, directory: str | Path, *, stem: str | None = None
    ) -> dict[str, Path]:
        """Export all supported formats from the same normalized result."""

        output = Path(directory).expanduser().resolve()
        output.mkdir(parents=True, exist_ok=True)
        name = stem or self.result.analysis_id
        return {
            "markdown": self.to_markdown(output / f"{name}.md"),
            "excel": self.to_excel(output / f"{name}.xlsx"),
            "pdf": self.to_pdf(output / f"{name}.pdf"),
        }

    def export_bundle(
        self, directory: str | Path, *, stem: str | None = None
    ) -> dict[str, Path]:
        """Export all reports plus the standalone traceability manifest."""

        artifacts = self.export_all(directory, stem=stem)
        output = Path(directory).expanduser().resolve()
        name = stem or self.result.analysis_id
        artifacts["manifest"] = self.manifest.export(output / f"{name}.manifest.json")
        return artifacts

    @staticmethod
    def _target(path: str | Path, suffix: str) -> Path:
        target = Path(path).expanduser().resolve()
        if target.suffix.lower() != suffix:
            raise ValueError(f"report path must use {suffix}")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target


def _cell(reference: str, value: Any, style: int = 0) -> str:
    text = escape(_display(value))
    return f'<c r="{reference}" t="inlineStr" s="{style}"><is><t>{text}</t></is></c>'


def _worksheet(title: str, section: str, rows: list[tuple[str, Any]]) -> str:
    data = [
        f'<row r="1" ht="28" customHeight="1">{_cell("A1", title, 1)}</row>',
        f'<row r="2" ht="22" customHeight="1">{_cell("A2", section, 2)}</row>',
        f'<row r="4">{_cell("A4", "Field", 3)}{_cell("B4", "Value", 3)}</row>',
    ]
    for number, (key, value) in enumerate(rows, 5):
        style = 4 if number % 2 else 5
        data.append(
            f'<row r="{number}">{_cell(f"A{number}", key, style)}{_cell(f"B{number}", value, style)}</row>'
        )
    last = max(4, len(rows) + 4)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetViews><sheetView showGridLines="0" workbookViewId="0"/></sheetViews>'
        '<cols><col min="1" max="1" width="52" customWidth="1"/><col min="2" max="2" width="68" customWidth="1"/></cols>'
        f'<sheetData>{"".join(data)}</sheetData><autoFilter ref="A4:B{last}"/>'
        '<mergeCells count="2"><mergeCell ref="A1:B1"/><mergeCell ref="A2:B2"/></mergeCells>'
        "</worksheet>"
    )


def _content_types(count: int) -> str:
    sheets = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        + sheets
        + "</Types>"
    )


def _root_relationships() -> str:
    return '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'


def _workbook(names: list[str]) -> str:
    sheets = "".join(
        f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>'
        for i, name in enumerate(names, 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
        + sheets
        + "</sheets></workbook>"
    )


def _workbook_relationships(count: int) -> str:
    rels = "".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, count + 1)
    )
    rels += f'<Relationship Id="rId{count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + rels
        + "</Relationships>"
    )


def _styles() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="4"><font><sz val="10"/><name val="Aptos"/></font><font><b/><sz val="16"/><color rgb="FFFFFFFF"/><name val="Aptos Display"/></font><font><b/><sz val="12"/><color rgb="FF12344D"/><name val="Aptos Display"/></font><font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Aptos"/></font></fonts><fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF12344D"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FF176B87"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFF2F6F8"/></patternFill></fill></fills><borders count="2"><border/><border><bottom style="thin"><color rgb="FFD6E1E6"/></bottom></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="6"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf><xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="3" fillId="3" borderId="0" xfId="0"/><xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>"""


__all__ = [
    "AssessmentCriteria",
    "EngineeringAssessment",
    "EngineeringCheck",
    "EngineeringReport",
    "ReportTemplate",
]
