"""Unified traceability records for OffshoreSafe engineering results."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from offshoresafe.analysis.workflow import EngineeringAnalysisResult

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class TraceabilityValidation:
    """Completeness and integrity status for one traceability manifest."""

    complete: bool
    missing_fields: tuple[str, ...]
    invalid_fields: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TraceabilityManifest:
    """Analysis-independent, review-ready provenance for one result."""

    project_id: str
    analysis_id: str
    analysis_type: str
    method: str
    solver_id: str
    adapter: str
    solver_version: str | None
    software_version: str
    timestamp: str
    project_source_file: str | None
    input_source_file: str | None
    output_source_file: str | None
    input_file_hash: str | None
    output_file_hash: str | None
    case_id: str | None
    sample_id: str | None
    parameters_hash: str
    payload_hash: str
    result_hash: str
    schema_version: str = "1.0"

    @classmethod
    def from_result(cls, result: EngineeringAnalysisResult) -> TraceabilityManifest:
        """Normalize nested solver provenance and calculate stable fingerprints."""

        if not isinstance(result, EngineeringAnalysisResult):
            raise TypeError("result must be an EngineeringAnalysisResult")
        trace = result.traceability
        solver_input = trace.get("solver_input", {})
        solver_output = trace.get("solver_output", {})
        context = trace.get("context", {})
        if not isinstance(solver_input, Mapping):
            solver_input = {}
        if not isinstance(solver_output, Mapping):
            solver_output = {}
        if not isinstance(context, Mapping):
            context = {}
        parameters_hash = _digest(result.to_dict()["parameters"])
        payload_hash = _digest(result.to_dict()["payload"])
        core = {
            "schema_version": result.schema_version,
            "project_id": result.project_id,
            "analysis_id": result.analysis_id,
            "analysis_type": result.analysis_type,
            "method": result.method,
            "solver_id": result.solver_id,
            "adapter": result.adapter,
            "software_version": result.software_version,
            "analyzed_at": result.analyzed_at,
            "parameters_hash": parameters_hash,
            "payload_hash": payload_hash,
            "input_file_hash": solver_input.get("input_file_hash"),
            "output_file_hash": solver_output.get("output_file_hash"),
        }
        return cls(
            project_id=result.project_id,
            analysis_id=result.analysis_id,
            analysis_type=result.analysis_type,
            method=result.method,
            solver_id=result.solver_id,
            adapter=result.adapter,
            solver_version=(
                solver_output.get("solver_version")
                or solver_input.get("solver_version")
            ),
            software_version=result.software_version,
            timestamp=result.analyzed_at,
            project_source_file=trace.get("project_source_file"),
            input_source_file=solver_input.get("source_file"),
            output_source_file=solver_output.get("source_file"),
            input_file_hash=solver_input.get("input_file_hash"),
            output_file_hash=solver_output.get("output_file_hash"),
            case_id=context.get("case_id"),
            sample_id=context.get("sample_id"),
            parameters_hash=parameters_hash,
            payload_hash=payload_hash,
            result_hash=_digest(core),
        )

    def validate(self) -> TraceabilityValidation:
        """Check certification-critical fields without rejecting legacy results."""

        required = {
            "project_id": self.project_id,
            "analysis_id": self.analysis_id,
            "analysis_type": self.analysis_type,
            "method": self.method,
            "solver_id": self.solver_id,
            "adapter": self.adapter,
            "software_version": self.software_version,
            "timestamp": self.timestamp,
            "input_file_hash": self.input_file_hash,
            "output_file_hash": self.output_file_hash,
        }
        missing = tuple(name for name, value in required.items() if not value)
        hashes = {
            "input_file_hash": self.input_file_hash,
            "output_file_hash": self.output_file_hash,
            "parameters_hash": self.parameters_hash,
            "payload_hash": self.payload_hash,
            "result_hash": self.result_hash,
        }
        invalid = tuple(
            name for name, value in hashes.items() if value and not _SHA256.fullmatch(value)
        )
        warnings = tuple(
            f"{name} is not available"
            for name, value in (("case_id", self.case_id), ("sample_id", self.sample_id))
            if not value
        )
        return TraceabilityValidation(not missing and not invalid, missing, invalid, warnings)

    def to_dict(self) -> dict[str, Any]:
        """Return a stable serializable representation including validation."""

        validation = self.validate()
        data = {name: getattr(self, name) for name in self.__dataclass_fields__}
        data["validation"] = {
            "complete": validation.complete,
            "missing_fields": list(validation.missing_fields),
            "invalid_fields": list(validation.invalid_fields),
            "warnings": list(validation.warnings),
        }
        return data


__all__ = ["TraceabilityManifest", "TraceabilityValidation"]
