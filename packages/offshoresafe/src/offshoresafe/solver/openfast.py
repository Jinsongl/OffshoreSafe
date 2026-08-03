"""OpenFAST input and ASCII output adapter."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar

from offshoresafe.solver.base import SolverAdapter
from offshoresafe.solver.result import SolverResult

_VERSION_PATTERN = re.compile(
    r"\b(?:OpenFAST|FAST)\s*(?:v(?:ersion)?\s*)?"
    r"(?P<version>\d+(?:\.\d+){0,3})\b",
    re.IGNORECASE,
)
_INPUT_PATTERN = re.compile(
    r'^\s*(?P<value>"[^"]*"|\'[^\']*\'|\S+)\s+'
    r"(?P<key>[A-Za-z][A-Za-z0-9_]*)\s*(?:-\s*.*)?$"
)


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _solver_version(lines: list[str]) -> str | None:
    for line in lines:
        match = _VERSION_PATTERN.search(line)
        if match:
            return match.group("version")
    return None


def _coerce_input_value(raw: str) -> str | bool | int | float:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value.replace("D", "E").replace("d", "e"))
        except ValueError:
            return value


def _unit_name(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and (value[0], value[-1]) in {("(", ")"), ("[", "]")}:
        return value[1:-1]
    return value


class OpenFASTAdapter(SolverAdapter):
    """Read OpenFAST primary input files and tabular ASCII ``.out`` files."""

    name = "openfast"
    channel_map: ClassVar[Mapping[str, str]] = MappingProxyType(
        {
            "Wind1VelX": "wind_speed",
            "RotSpeed": "rotor_speed",
            "GenSpeed": "generator_speed",
            "GenPwr": "generator_power",
            "RootMxb1": "blade_1_root_edge_moment",
            "RootMyb1": "blade_1_root_flap_moment",
            "RootMxb2": "blade_2_root_edge_moment",
            "RootMyb2": "blade_2_root_flap_moment",
            "RootMxb3": "blade_3_root_edge_moment",
            "RootMyb3": "blade_3_root_flap_moment",
            "TwrBsMxt": "tower_base_side_side_moment",
            "TwrBsMyt": "tower_base_fore_aft_moment",
            "PtfmSurge": "platform_surge",
            "PtfmSway": "platform_sway",
            "PtfmHeave": "platform_heave",
            "PtfmRoll": "platform_roll",
            "PtfmPitch": "platform_pitch",
            "PtfmYaw": "platform_yaw",
        }
    )

    def read_input(self, path: str | Path) -> MappingProxyType[str, Any]:
        """Read scalar parameters and traceability metadata from a primary file."""

        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"OpenFAST input file does not exist: {source}")
        lines = _read_text(source).splitlines()
        parameters: dict[str, Any] = {}
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith(("!", "#", "---")):
                continue
            match = _INPUT_PATTERN.match(line)
            if match:
                parameters[match.group("key")] = _coerce_input_value(
                    match.group("value")
                )

        return MappingProxyType(
            {
                "adapter": self.name,
                "solver": "OpenFAST",
                "solver_version": _solver_version(lines),
                "source_file": str(source),
                "input_file_hash": _file_hash(source),
                "parameters": MappingProxyType(parameters),
            }
        )

    def read_output(self, path: str | Path) -> SolverResult:
        """Read an OpenFAST whitespace-delimited ASCII output file."""

        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"OpenFAST output file does not exist: {source}")
        if source.suffix.lower() == ".outb":
            raise ValueError(
                "binary OpenFAST .outb files are not supported by this adapter; "
                "configure OpenFAST for ASCII .out output"
            )

        lines = _read_text(source).splitlines()
        header_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.split() and line.split()[0].lower() == "time"
            ),
            None,
        )
        if header_index is None or header_index + 1 >= len(lines):
            raise ValueError("OpenFAST output is missing Time and units header rows")

        source_names = lines[header_index].split()
        source_units = lines[header_index + 1].split()
        if len(source_names) < 2 or len(source_units) != len(source_names):
            raise ValueError("OpenFAST channel and unit columns do not match")

        canonical_names = [self.map_channel(name) for name in source_names[1:]]
        if len(set(canonical_names)) != len(canonical_names):
            raise ValueError("OpenFAST channel mapping produced duplicate names")

        columns: list[list[float]] = [[] for _ in source_names]
        for line_number, line in enumerate(lines[header_index + 2 :], header_index + 3):
            if not line.strip():
                continue
            values = line.split()
            if len(values) != len(source_names):
                raise ValueError(
                    f"OpenFAST output line {line_number} has {len(values)} columns; "
                    f"expected {len(source_names)}"
                )
            try:
                numeric = [
                    float(value.replace("D", "E").replace("d", "e")) for value in values
                ]
            except ValueError as error:
                raise ValueError(
                    f"OpenFAST output line {line_number} contains non-numeric data"
                ) from error
            for column, value in zip(columns, numeric):
                column.append(value)

        if not columns[0]:
            raise ValueError("OpenFAST output contains no time-series rows")

        units = {
            canonical: _unit_name(unit)
            for canonical, unit in zip(canonical_names, source_units[1:])
        }
        metadata = {
            "adapter": self.name,
            "solver": "OpenFAST",
            "solver_version": _solver_version(lines[:header_index]),
            "source_file": str(source),
            "source_format": "openfast-ascii",
            "output_file_hash": _file_hash(source),
            "source_channels": tuple(source_names[1:]),
        }
        return SolverResult(
            time=columns[0],
            channels={
                name: values for name, values in zip(canonical_names, columns[1:])
            },
            units=units,
            metadata=metadata,
        )

    def export_result(self, result: SolverResult, path: str | Path) -> Path:
        """Export a normalized result as JSON without solver-specific fields."""

        target = Path(path).expanduser().resolve()
        if target.suffix.lower() != ".json":
            raise ValueError("OpenFAST normalized exports must use a .json path")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "time": list(result.time),
            "channels": {
                name: list(values) for name, values in result.channels.items()
            },
            "units": dict(result.units),
            "metadata": dict(result.metadata),
        }
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        return target
