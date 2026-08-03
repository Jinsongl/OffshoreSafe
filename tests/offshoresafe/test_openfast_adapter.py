"""Issue #052 OpenFAST adapter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from offshoresafe import OpenFASTAdapter, SolverResult

ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "benchmarks" / "offshore" / "openfast_adapter"
INPUT = FIXTURE / "input" / "main.fst"
OUTPUT = FIXTURE / "output" / "main.out"


def test_read_input_extracts_parameters_version_and_hash() -> None:
    data = OpenFASTAdapter().read_input(INPUT)

    assert data["adapter"] == "openfast"
    assert data["solver"] == "OpenFAST"
    assert data["solver_version"] == "3.5.3"
    assert data["parameters"] == {
        "Echo": False,
        "TurbineName": "IEA-15-240-RWT",
        "DT": 0.0125,
        "TMax": 1.0,
        "EDFile": "ElastoDyn.dat",
    }
    assert len(data["input_file_hash"]) == 64
    with pytest.raises(TypeError):
        data["parameters"]["DT"] = 1.0


def test_read_ascii_output_normalizes_channels_units_and_metadata() -> None:
    result = OpenFASTAdapter().read_output(OUTPUT)

    assert result.time == (0.0, 0.5, 1.0)
    assert result.channel_names == (
        "wind_speed",
        "rotor_speed",
        "generator_power",
        "tower_base_fore_aft_moment",
        "platform_pitch",
    )
    assert result.channels["tower_base_fore_aft_moment"][-1] == 22_000.0
    assert result.units["wind_speed"] == "m/s"
    assert result.units["tower_base_fore_aft_moment"] == "kN-m"
    assert result.metadata["solver_version"] == "3.5.3"
    assert result.metadata["source_format"] == "openfast-ascii"
    assert result.metadata["source_channels"] == (
        "Wind1VelX",
        "RotSpeed",
        "GenPwr",
        "TwrBsMyt",
        "PtfmPitch",
    )
    assert len(result.metadata["output_file_hash"]) == 64


def test_read_output_accepts_fortran_exponents_and_unmapped_channels(
    tmp_path: Path,
) -> None:
    output = tmp_path / "fortran.out"
    output.write_text(
        "OpenFAST v3.4.1\nTime Custom\n(s) (-)\n0.0 1.0D+00\n1.0 2.0d+00\n",
        encoding="utf-8",
    )

    result = OpenFASTAdapter().read_output(output)
    assert result.channels["Custom"] == (1.0, 2.0)
    assert result.units["Custom"] == "-"


def test_export_result_preserves_normalized_payload(tmp_path: Path) -> None:
    adapter = OpenFASTAdapter()
    result = adapter.read_output(OUTPUT)
    target = adapter.export_result(result, tmp_path / "normalized.json")
    payload = json.loads(target.read_text(encoding="utf-8"))

    assert payload["time"] == [0.0, 0.5, 1.0]
    assert payload["channels"]["generator_power"] == [1000.0, 1050.0, 1100.0]
    assert payload["metadata"]["adapter"] == "openfast"

    with pytest.raises(ValueError, match=r"\.json"):
        adapter.export_result(result, tmp_path / "normalized.csv")


def test_read_output_rejects_binary_and_malformed_files(tmp_path: Path) -> None:
    binary = tmp_path / "result.outb"
    binary.write_bytes(b"binary")
    with pytest.raises(ValueError, match=r"ASCII \.out"):
        OpenFASTAdapter().read_output(binary)

    malformed = tmp_path / "malformed.out"
    malformed.write_text(
        "OpenFAST v3.5.3\nTime RotSpeed\n(s) (rpm)\n0.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="line 4 has 1 columns; expected 2"):
        OpenFASTAdapter().read_output(malformed)


def test_file_errors_are_clear(tmp_path: Path) -> None:
    adapter = OpenFASTAdapter()
    with pytest.raises(FileNotFoundError, match="input file"):
        adapter.read_input(tmp_path / "missing.fst")
    with pytest.raises(FileNotFoundError, match="output file"):
        adapter.read_output(tmp_path / "missing.out")


def test_result_contract_rejects_non_increasing_openfast_time() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        SolverResult(time=[0.0, 0.0], channels={"rotor_speed": [8.0, 8.1]})
