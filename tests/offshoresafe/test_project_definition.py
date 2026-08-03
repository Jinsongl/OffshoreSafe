"""Issue #050 project definition and YAML contract tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from offshoresafe import OffshoreProject, load_project
from pydantic import ValidationError

ROOT = Path(__file__).parents[2]
EXAMPLE = ROOT / "examples" / "projects" / "minimal" / "project.yaml"


def test_minimal_example_loads_and_resolves_relative_paths() -> None:
    project = load_project(EXAMPLE)

    assert project.schema_version == "1.0"
    assert project.project.project_id == "demo-offshore-wind"
    assert project.turbine.definition_file.is_absolute()
    assert project.turbine.definition_file.name == "turbine.yaml"
    assert project.solver.input_file.name == "main.fst"
    assert project.analyses[0].backend == "native"
    assert project.source_file == EXAMPLE.resolve()


def test_unknown_fields_and_invalid_version_are_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["unknown"] = True
    data["schema_version"] = "2.0"
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError) as captured:
        load_project(path, check_paths=False)

    errors = captured.value.errors()
    assert {tuple(error["loc"]) for error in errors} >= {
        ("schema_version",),
        ("unknown",),
    }


def test_duplicate_analysis_ids_are_rejected(tmp_path: Path) -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["analyses"].append(dict(data["analyses"][0]))
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValidationError, match="analysis_id values must be unique"):
        load_project(path, check_paths=False)


def test_missing_referenced_file_has_field_level_error(tmp_path: Path) -> None:
    data = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
    data["turbine"]["definition_file"] = "missing.yaml"
    path = tmp_path / "project.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValueError, match=r"turbine\.definition_file.*missing.yaml"):
        load_project(path)


def test_yaml_round_trip_preserves_definition_and_portable_paths(
    tmp_path: Path,
) -> None:
    original = load_project(EXAMPLE)
    target = tmp_path / "copy" / "project.yaml"
    original.save(target)
    serialized = yaml.safe_load(target.read_text(encoding="utf-8"))
    reloaded = OffshoreProject.load(target)

    turbine_path = Path(serialized["turbine"]["definition_file"])
    solver_path = Path(serialized["solver"]["input_file"])
    same_volume = (
        target.drive.casefold() == original.turbine.definition_file.drive.casefold()
    )
    assert turbine_path.is_absolute() is not same_volume
    assert solver_path.is_absolute() is not same_volume
    assert reloaded.to_dict() == original.to_dict()


def test_project_package_depends_on_uqra_without_reverse_import() -> None:
    import offshoresafe
    import uqra

    assert offshoresafe.__version__
    assert uqra.__version__
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, uqra; assert 'offshoresafe' not in sys.modules",
        ],
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "packages" / "uqra" / "src"),
        },
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr
