"""Issue #064 end-to-end engineering analysis workflow tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from offshoresafe import (
    EngineeringAnalysisResult,
    EngineeringAnalysisWorkflow,
    OffshoreProject,
)

ROOT = Path(__file__).parents[2]
OPENFAST_INPUT = (
    ROOT / "benchmarks" / "offshore" / "openfast_adapter" / "input" / "main.fst"
)
HEROWIND_INPUT = (
    ROOT / "benchmarks" / "offshore" / "herowind_adapter" / "input" / "case.yaml"
)
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def _project_file(tmp_path: Path, adapter: str, output: Path) -> Path:
    turbine = tmp_path / "turbine.yaml"
    turbine.write_text("model: test\n", encoding="utf-8")
    input_file = OPENFAST_INPUT if adapter == "openfast" else HEROWIND_INPUT
    data = {
        "schema_version": "1.0",
        "project": {"project_id": "workflow-test", "name": "Workflow test"},
        "turbine": {
            "turbine_id": "test-turbine",
            "model": "Test turbine",
            "rated_power_mw": 15.0,
            "definition_file": str(turbine),
        },
        "solver": {
            "solver_id": f"{adapter}-primary",
            "adapter": adapter,
            "input_file": str(input_file),
            "output_file": str(output),
        },
        "analyses": [
            {
                "analysis_id": "loads-statistics",
                "analysis_type": "statistics",
                "method": "descriptive",
                "settings": {"channels": ["tower_base_fore_aft_moment"]},
            },
            {
                "analysis_id": "tower-extreme",
                "analysis_type": "extreme",
                "method": "gumbel",
                "settings": {
                    "channel": "tower_base_fore_aft_moment",
                    "distribution": "gumbel",
                    "return_period": 50.0,
                    "events_per_period": 12.0,
                },
            },
            {
                "analysis_id": "tower-fatigue",
                "analysis_type": "fatigue",
                "method": "rainflow-miner-del",
                "settings": {
                    "channel": "tower_base_fore_aft_moment",
                    "slope": 3.0,
                    "log10_intercept": 15.0,
                    "equivalent_cycles": 100.0,
                },
            },
        ],
    }
    path = tmp_path / f"{adapter}-project.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _openfast_output(path: Path) -> None:
    path.write_text(
        "OpenFAST v3.5.3\n"
        "Time TwrBsMyt\n"
        "(s) (kN-m)\n"
        "0 0\n1 10\n2 0\n3 20\n4 0\n5 15\n6 0\n",
        encoding="utf-8",
    )


def _herowind_output(path: Path) -> None:
    path.write_text(
        "time (s), TwrBsMyt (kN-m)\n0 0\n1 10\n2 0\n3 20\n4 0\n5 15\n6 0\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("adapter", "writer"),
    [("openfast", _openfast_output), ("herowind", _herowind_output)],
)
def test_same_configured_analyses_run_over_normalized_solver_results(
    tmp_path: Path, adapter: str, writer: object
) -> None:
    output = tmp_path / ("loads.out" if adapter == "openfast" else "loads.txt")
    writer(output)  # type: ignore[operator]
    project = OffshoreProject.load(_project_file(tmp_path, adapter, output))
    workflow = EngineeringAnalysisWorkflow(project)

    statistics = workflow.run("loads-statistics", analyzed_at=FIXED_TIME)
    extreme = workflow.run("tower-extreme", analyzed_at=FIXED_TIME)
    fatigue = workflow.run("tower-fatigue", analyzed_at=FIXED_TIME)

    channel = statistics.payload["channels"]["tower_base_fore_aft_moment"]
    assert channel["maximum"] == 20.0
    assert extreme.payload["sample_count"] == 3
    assert extreme.payload["return_period_response"] > 20.0
    assert fatigue.payload["damage"] > 0.0
    assert fatigue.payload["damage_equivalent_load"] > 0.0
    assert statistics.project_id == "workflow-test"
    assert statistics.adapter == adapter
    assert statistics.traceability["solver_input"]["input_file_hash"]
    assert statistics.traceability["solver_output"]["output_file_hash"]


def test_export_is_deterministic_and_round_trips(tmp_path: Path) -> None:
    output = tmp_path / "loads.out"
    _openfast_output(output)
    project = OffshoreProject.load(_project_file(tmp_path, "openfast", output))
    workflow = EngineeringAnalysisWorkflow(project)
    result = workflow.run("tower-extreme", analyzed_at=FIXED_TIME)

    first = workflow.export_result(result, tmp_path / "first.json")
    second = workflow.export_result(result, tmp_path / "second.json")
    restored = EngineeringAnalysisResult.load(first)
    project_copy = tmp_path / "copy" / "project.yaml"
    project.save(project_copy)
    reloaded_project = OffshoreProject.load(project_copy)

    assert first.read_bytes() == second.read_bytes()
    assert restored.to_dict() == result.to_dict()
    assert reloaded_project.solver.output_file == output.resolve()
    with pytest.raises(TypeError):
        restored.payload["channel"] = "changed"  # type: ignore[index]


def test_output_override_and_actionable_configuration_errors(tmp_path: Path) -> None:
    output = tmp_path / "loads.out"
    _openfast_output(output)
    project = OffshoreProject.load(_project_file(tmp_path, "openfast", output))
    project_without_output = project.model_copy(
        update={"solver": project.solver.model_copy(update={"output_file": None})}
    )
    workflow = EngineeringAnalysisWorkflow(project_without_output)

    assert workflow.run(
        "loads-statistics", output_file=output, analyzed_at=FIXED_TIME
    ).payload
    with pytest.raises(ValueError, match="output_file is required"):
        workflow.run("loads-statistics", analyzed_at=FIXED_TIME)
    with pytest.raises(KeyError, match="unknown project analysis"):
        workflow.run("missing", output_file=output, analyzed_at=FIXED_TIME)


def test_unsupported_analysis_and_settings_are_rejected(tmp_path: Path) -> None:
    output = tmp_path / "loads.out"
    _openfast_output(output)
    project = OffshoreProject.load(_project_file(tmp_path, "openfast", output))
    bad_analysis = project.analyses[0].model_copy(update={"analysis_type": "unknown"})
    bad_project = project.model_copy(update={"analyses": (bad_analysis,)})
    with pytest.raises(ValueError, match="unsupported engineering analysis_type"):
        EngineeringAnalysisWorkflow(bad_project).run(
            bad_analysis.analysis_id, analyzed_at=FIXED_TIME
        )

    bad_settings = project.analyses[0].model_copy(update={"settings": {"bad": 1}})
    bad_project = project.model_copy(update={"analyses": (bad_settings,)})
    with pytest.raises(ValueError, match="unsupported statistics settings"):
        EngineeringAnalysisWorkflow(bad_project).run(
            bad_settings.analysis_id, analyzed_at=FIXED_TIME
        )
