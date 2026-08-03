"""YAML loading, path resolution, and serialization for OffshoreSafe projects."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from offshoresafe.project.definition import OffshoreProject


def _resolve_file(value: Path, base_directory: Path, field: str, check: bool) -> Path:
    path = value if value.is_absolute() else base_directory / value
    path = path.resolve()
    if check and not path.is_file():
        raise ValueError(f"{field} does not exist or is not a file: {path}")
    return path


def load_project(path: str | Path, *, check_paths: bool = True) -> OffshoreProject:
    """Load a strict project definition and resolve its file references."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"project file does not exist: {source}")
    try:
        raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid project YAML: {error}") from error
    if not isinstance(raw, Mapping):
        raise ValueError("project YAML root must be a mapping")
    project = OffshoreProject.model_validate(dict(raw))
    turbine = project.turbine.model_copy(
        update={
            "definition_file": _resolve_file(
                project.turbine.definition_file,
                source.parent,
                "turbine.definition_file",
                check_paths,
            )
        }
    )
    solver = project.solver.model_copy(
        update={
            "input_file": _resolve_file(
                project.solver.input_file,
                source.parent,
                "solver.input_file",
                check_paths,
            ),
            "output_file": (
                _resolve_file(
                    project.solver.output_file,
                    source.parent,
                    "solver.output_file",
                    check_paths,
                )
                if project.solver.output_file is not None
                else None
            ),
        }
    )
    return project.model_copy(
        update={"turbine": turbine, "solver": solver, "source_file": source}
    )


def _relative(path: Path, directory: Path) -> str:
    try:
        return os.path.relpath(path, directory).replace("\\", "/")
    except ValueError:
        return path.as_posix()


def save_project(project: OffshoreProject, path: str | Path) -> Path:
    """Write a project YAML file with portable relative file references."""
    if not isinstance(project, OffshoreProject):
        raise TypeError("project must be an OffshoreProject")
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = project.to_dict()
    data["turbine"]["definition_file"] = _relative(
        project.turbine.definition_file, target.parent
    )
    data["solver"]["input_file"] = _relative(project.solver.input_file, target.parent)
    if project.solver.output_file is not None:
        data["solver"]["output_file"] = _relative(
            project.solver.output_file, target.parent
        )
    else:
        data["solver"].pop("output_file", None)
    target.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return target


__all__ = ["load_project", "save_project"]
