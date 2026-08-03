"""Issue #051 solver adapter contract tests."""

from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar

import pytest
from offshoresafe import SolverAdapter, SolverCapability, SolverResult


class CsvFixtureAdapter(SolverAdapter):
    """Small concrete adapter used to exercise the public contract."""

    name = "csv-fixture"
    channel_map: ClassVar[Mapping[str, str]] = {
        "Time": "time",
        "RotSpeed": "rotor_speed",
    }

    def read_input(self, path: str | Path) -> Mapping[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def read_output(self, path: str | Path) -> SolverResult:
        with Path(path).open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        source_channels = tuple(name for name in rows[0] if name != "Time")
        return SolverResult(
            time=[float(row["Time"]) for row in rows],
            channels={
                self.map_channel(name): [float(row[name]) for row in rows]
                for name in source_channels
            },
            units={"rotor_speed": "rpm"},
            metadata={"adapter": self.name},
        )

    def export_result(self, result: SolverResult, path: str | Path) -> Path:
        target = Path(path).resolve()
        with target.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("time", *result.channel_names))
            for index, time in enumerate(result.time):
                writer.writerow(
                    (
                        time,
                        *(
                            result.channels[name][index]
                            for name in result.channel_names
                        ),
                    )
                )
        return target


def test_abstract_adapter_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        SolverAdapter()  # type: ignore[abstract]


def test_channel_mapping_and_capability_detection() -> None:
    adapter = CsvFixtureAdapter()

    assert adapter.map_channel("RotSpeed") == "rotor_speed"
    assert adapter.map_channel("Unknown") == "Unknown"
    assert adapter.supports(SolverCapability.READ_OUTPUT)
    assert adapter.supports("export_result")
    assert not adapter.supports("run")

    with pytest.raises(ValueError, match="non-empty"):
        adapter.map_channel(" ")


def test_result_normalizes_sequences_and_is_immutable() -> None:
    source = [1.0, 2.0]
    result = SolverResult(
        time=[0, 1],
        channels={"load": source},
        units={"load": "kN"},
        metadata={"solver": "fixture"},
    )
    source[0] = 99.0

    assert result.time == (0.0, 1.0)
    assert result.channels["load"] == (1.0, 2.0)
    assert result.sample_count == 2
    assert result.channel_names == ("load",)
    with pytest.raises(TypeError):
        result.channels["other"] = (0.0, 0.0)  # type: ignore[index]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"time": [], "channels": {"x": []}}, "time must not be empty"),
        ({"time": [0, 0], "channels": {"x": [1, 2]}}, "strictly increasing"),
        ({"time": [0, 1], "channels": {"x": [1]}}, "expected 2"),
        (
            {"time": [0, 1], "channels": {"x": [1, float("nan")]}},
            "finite values",
        ),
        (
            {"time": [0, 1], "channels": {"x": [1, 2]}, "units": {"y": "m"}},
            "unknown channels",
        ),
    ],
)
def test_result_rejects_invalid_time_series(
    kwargs: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SolverResult(**kwargs)  # type: ignore[arg-type]


def test_adapter_read_map_export_round_trip(tmp_path: Path) -> None:
    adapter = CsvFixtureAdapter()
    input_path = tmp_path / "input.json"
    input_path.write_text('{"solver_version": "1.2"}', encoding="utf-8")
    output_path = tmp_path / "solver.csv"
    output_path.write_text("Time,RotSpeed\n0,8\n1,9\n", encoding="utf-8")

    assert adapter.read_input(input_path)["solver_version"] == "1.2"
    result = adapter.read_output(output_path)
    assert result.channel_names == ("rotor_speed",)
    assert result.channels["rotor_speed"] == (8.0, 9.0)
    assert result.metadata["adapter"] == "csv-fixture"

    exported = adapter.export_result(result, tmp_path / "normalized.csv")
    assert exported.is_absolute()
    assert exported.read_text(encoding="utf-8").splitlines() == [
        "time,rotor_speed",
        "0.0,8.0",
        "1.0,9.0",
    ]
