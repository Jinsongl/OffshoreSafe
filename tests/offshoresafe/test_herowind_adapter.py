"""Issue #053 HEROWIND adapter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from offshoresafe import HEROWINDAdapter

ROOT = Path(__file__).parents[2]
CASE = ROOT / "benchmarks" / "offshore" / "herowind_adapter"


def test_read_input_yaml_and_traceability() -> None:
    data = HEROWINDAdapter().read_input(CASE / "input" / "case.yaml")
    assert data["configuration"]["case_id"] == "dlc-1.1"
    assert len(data["input_file_hash"]) == 64
    with pytest.raises(TypeError):
        data["configuration"]["case_id"] = "changed"


def test_read_result_unifies_channels_units_and_metadata() -> None:
    result = HEROWINDAdapter().read_output(CASE / "output" / "MultibodyOutput.txt")
    assert result.time == (0.0, 0.5, 1.0)
    assert result.channel_names == (
        "wind_speed",
        "rotor_speed",
        "tower_base_fore_aft_moment",
        "TipDxc1",
    )
    assert result.units["tower_base_fore_aft_moment"] == "kN-m"
    assert result.channels["tower_base_fore_aft_moment"][-1] == 22_000.0
    assert result.metadata["source_channels"][-1] == "TipDxc1"
    assert len(result.metadata["output_file_hash"]) == 64


def test_comma_data_and_fortran_exponents_are_supported(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    path.write_text("time (s), Custom (-)\n0,1D+00\n1,2d+00\n", encoding="utf-8")
    result = HEROWINDAdapter().read_output(path)
    assert result.channels["Custom"] == (1.0, 2.0)


def test_malformed_results_have_actionable_errors(tmp_path: Path) -> None:
    missing_time = tmp_path / "missing-time.txt"
    missing_time.write_text("step, Load\n0 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="first channel must be time"):
        HEROWINDAdapter().read_output(missing_time)

    bad_row = tmp_path / "bad-row.txt"
    bad_row.write_text("time, Load\n0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 2 has 1 columns; expected 2"):
        HEROWINDAdapter().read_output(bad_row)


def test_export_result_is_portable_json(tmp_path: Path) -> None:
    adapter = HEROWINDAdapter()
    result = adapter.read_output(CASE / "output" / "MultibodyOutput.txt")
    target = adapter.export_result(result, tmp_path / "result.json")
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["channels"]["wind_speed"] == [10.0, 10.5, 11.0]
    with pytest.raises(ValueError, match=r"\.json"):
        adapter.export_result(result, tmp_path / "result.csv")
