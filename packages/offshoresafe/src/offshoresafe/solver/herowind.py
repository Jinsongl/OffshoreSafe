"""HEROWIND text result adapter."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar

import yaml

from offshoresafe.solver.base import SolverAdapter
from offshoresafe.solver.openfast import OpenFASTAdapter
from offshoresafe.solver.result import SolverResult

_HEADER = re.compile(r"^\s*(?P<name>.*?)\s*(?:\((?P<unit>[^()]*)\))?\s*$")


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class HEROWINDAdapter(SolverAdapter):
    """Normalize HEROWIND comma-header text result files."""

    name = "herowind"
    channel_map: ClassVar[Mapping[str, str]] = MappingProxyType(
        dict(OpenFASTAdapter.channel_map)
    )

    def read_input(self, path: str | Path) -> Mapping[str, Any]:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"HEROWIND input file does not exist: {source}")
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("HEROWIND YAML input must contain a mapping")
        return MappingProxyType(
            {
                "adapter": self.name,
                "solver": "HEROWIND",
                "source_file": str(source),
                "input_file_hash": _hash(source),
                "configuration": MappingProxyType(data),
            }
        )

    def read_output(self, path: str | Path) -> SolverResult:
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"HEROWIND result file does not exist: {source}")
        lines = [
            line.strip()
            for line in source.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
        if len(lines) < 2:
            raise ValueError("HEROWIND result must contain a header and data rows")
        fields = [field.strip() for field in lines[0].split(",")]
        parsed = [_HEADER.fullmatch(field) for field in fields]
        if any(match is None for match in parsed):
            raise ValueError("HEROWIND result contains an invalid channel header")
        names = [match.group("name").strip() for match in parsed if match]
        if names[0].lower() != "time":
            raise ValueError("HEROWIND result first channel must be time")
        canonical = [self.map_channel(name) for name in names[1:]]
        if len(set(canonical)) != len(canonical):
            raise ValueError("HEROWIND channel mapping produced duplicate names")
        columns: list[list[float]] = [[] for _ in names]
        for number, line in enumerate(lines[1:], 2):
            values = line.replace(",", " ").split()
            if len(values) != len(names):
                raise ValueError(
                    f"HEROWIND result line {number} has {len(values)} columns; expected {len(names)}"
                )
            try:
                numeric = [
                    float(value.replace("D", "E").replace("d", "e")) for value in values
                ]
            except ValueError as error:
                raise ValueError(
                    f"HEROWIND result line {number} contains non-numeric data"
                ) from error
            for column, value in zip(columns, numeric):
                column.append(value)
        units = {
            name: match.group("unit") or ""
            for name, match in zip(canonical, parsed[1:])
            if match
        }
        return SolverResult(
            time=columns[0],
            channels={name: values for name, values in zip(canonical, columns[1:])},
            units=units,
            metadata={
                "adapter": self.name,
                "solver": "HEROWIND",
                "source_file": str(source),
                "source_format": "herowind-text",
                "output_file_hash": _hash(source),
                "source_channels": tuple(names[1:]),
            },
        )

    def export_result(self, result: SolverResult, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        if target.suffix.lower() != ".json":
            raise ValueError("HEROWIND normalized exports must use a .json path")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "time": list(result.time),
            "channels": {
                name: list(values) for name, values in result.channels.items()
            },
            "units": dict(result.units),
            "metadata": dict(result.metadata),
        }
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return target
