"""Top-level OffshoreSafe project definition."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator

from offshoresafe.project.schema import (
    AnalysisConfiguration,
    ProjectInformation,
    SolverInformation,
    StrictModel,
    TurbineInformation,
)


class OffshoreProject(StrictModel):
    """Validated, versioned contents of an OffshoreSafe ``project.yaml``."""

    schema_version: Literal["1.0"] = "1.0"
    project: ProjectInformation
    turbine: TurbineInformation
    solver: SolverInformation
    analyses: tuple[AnalysisConfiguration, ...] = Field(min_length=1)
    source_file: Path | None = Field(default=None, exclude=True, repr=False)

    @model_validator(mode="after")
    def unique_analysis_ids(self) -> OffshoreProject:
        """Require stable unique identifiers within the analysis collection."""
        identifiers = [analysis.analysis_id for analysis in self.analyses]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("analysis_id values must be unique")
        return self

    @classmethod
    def load(cls, path: str | Path, *, check_paths: bool = True) -> OffshoreProject:
        """Load and validate a YAML project file."""
        from offshoresafe.project.loader import load_project

        return load_project(path, check_paths=check_paths)

    def save(self, path: str | Path) -> Path:
        """Serialize this project with paths relative to the target file."""
        from offshoresafe.project.loader import save_project

        return save_project(self, path)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation without runtime source state."""
        return self.model_dump(mode="json", exclude={"source_file"})


__all__ = ["OffshoreProject"]
