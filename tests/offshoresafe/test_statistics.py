"""Issue #060 engineering statistics tests."""

from __future__ import annotations

import math

import pytest
from offshoresafe import SolverResult, compute_statistics


@pytest.fixture
def solver_result() -> SolverResult:
    return SolverResult(
        time=[0.0, 1.0, 2.0, 3.0],
        channels={"load": [1.0, 2.0, 3.0, 4.0], "constant": [-2.0] * 4},
        units={"load": "kN", "constant": "m"},
        metadata={"adapter": "fixture", "output_file_hash": "abc123"},
    )


def test_population_statistics_match_analytical_values(
    solver_result: SolverResult,
) -> None:
    result = compute_statistics(solver_result)
    load = result["load"]

    assert load.count == 4
    assert load.mean == 2.5
    assert load.standard_deviation == pytest.approx(math.sqrt(1.25))
    assert load.minimum == 1.0
    assert load.maximum == 4.0
    assert load.rms == pytest.approx(math.sqrt(7.5))
    assert load.unit == "kN"

    constant = result["constant"]
    assert constant.mean == -2.0
    assert constant.standard_deviation == 0.0
    assert constant.rms == 2.0


def test_sample_standard_deviation_and_channel_selection(
    solver_result: SolverResult,
) -> None:
    result = compute_statistics(solver_result, ["load"], ddof=1)

    assert result.channel_names == ("load",)
    assert result["load"].standard_deviation == pytest.approx(math.sqrt(5 / 3))
    assert result.metadata["ddof"] == 1
    assert result.metadata["processing_method"] == "channel_statistics"
    assert result.metadata["output_file_hash"] == "abc123"


def test_results_are_read_only(solver_result: SolverResult) -> None:
    result = compute_statistics(solver_result)

    with pytest.raises(TypeError):
        result.channels["other"] = result["load"]  # type: ignore[index]
    with pytest.raises(TypeError):
        result.metadata["ddof"] = 2  # type: ignore[index]


@pytest.mark.parametrize("ddof", [-1, 1.5, True, 4])
def test_invalid_ddof_is_rejected(solver_result: SolverResult, ddof: object) -> None:
    with pytest.raises(ValueError, match="ddof"):
        compute_statistics(solver_result, ddof=ddof)  # type: ignore[arg-type]


def test_invalid_channel_selection_is_rejected(solver_result: SolverResult) -> None:
    with pytest.raises(ValueError, match="at least one"):
        compute_statistics(solver_result, [])
    with pytest.raises(ValueError, match="unique"):
        compute_statistics(solver_result, ["load", "load"])
    with pytest.raises(KeyError, match="missing"):
        compute_statistics(solver_result, ["missing"])
