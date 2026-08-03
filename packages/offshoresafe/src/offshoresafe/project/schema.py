"""Strict schema components for ``project.yaml``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

IDENTIFIER_PATTERN = r"^[A-Za-z][A-Za-z0-9_.-]*$"


class StrictModel(BaseModel):
    """Shared immutable, unknown-field-rejecting project model."""

    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class ProjectInformation(StrictModel):
    """Human and machine identity for one OffshoreSafe project."""

    project_id: str = Field(pattern=IDENTIFIER_PATTERN)
    name: str = Field(min_length=1)
    description: str | None = None
    organization: str | None = None


class TurbineInformation(StrictModel):
    """Offshore turbine definition referenced by the project."""

    turbine_id: str = Field(pattern=IDENTIFIER_PATTERN)
    model: str = Field(min_length=1)
    rated_power_mw: float = Field(gt=0.0)
    definition_file: Path


class SolverInformation(StrictModel):
    """External simulation solver and its project input file."""

    solver_id: str = Field(pattern=IDENTIFIER_PATTERN)
    adapter: str = Field(min_length=1)
    input_file: Path
    output_file: Path | None = None
    executable: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class AnalysisConfiguration(StrictModel):
    """One configured UQ, reliability, or engineering analysis."""

    analysis_id: str = Field(pattern=IDENTIFIER_PATTERN)
    analysis_type: str = Field(min_length=1)
    method: str = Field(min_length=1)
    backend: str = Field(default="native", min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)

    @field_validator("analysis_type", "method", "backend")
    @classmethod
    def normalize_algorithm_name(cls, value: str) -> str:
        """Reject whitespace-only values after global string stripping."""
        if not value:
            raise ValueError("must be a non-empty string")
        return value


__all__ = [
    "AnalysisConfiguration",
    "ProjectInformation",
    "SolverInformation",
    "TurbineInformation",
]
