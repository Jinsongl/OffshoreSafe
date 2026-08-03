"""Issue #071 blade fatigue reliability vertical-slice tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import yaml
from offshoresafe import (
    BladeFatigueLimitState,
    EngineeringAnalysisWorkflow,
    OffshoreProject,
    RainflowCycle,
    SolverResult,
    analyze_blade_fatigue_reliability,
    build_blade_fatigue_random_vector,
)

ROOT = Path(__file__).parents[2]
OPENFAST_INPUT = (
    ROOT / "benchmarks" / "offshore" / "openfast_adapter" / "input" / "main.fst"
)
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def _settings(**updates: object) -> dict[str, object]:
    settings: dict[str, object] = {
        "channel": "blade_1_root_flap_moment",
        "lifetime_repetitions": 50.0,
        "damage_limit": 1.0,
        "variables": {
            "load_factor": {
                "distribution": "Lognormal",
                "parameters": {"mean": 1.0, "std": 0.05},
            },
            "sn_slope": {
                "distribution": "Normal",
                "parameters": {"mean": 3.0, "std": 0.1},
            },
            "sn_log10_intercept": {
                "distribution": "Normal",
                "parameters": {"mean": 6.0, "std": 0.1},
            },
        },
    }
    settings.update(updates)
    return settings


def _solver_result() -> SolverResult:
    return SolverResult(
        time=range(7),
        channels={"blade_1_root_flap_moment": [0, 10, 0, 20, 0, 15, 0]},
        units={"blade_1_root_flap_moment": "kN-m"},
        metadata={"output_file_hash": "fixture-hash"},
    )


def test_blade_fatigue_limit_state_matches_miner_definition() -> None:
    cycles = (
        RainflowCycle(10.0, 5.0, 2.0),
        RainflowCycle(20.0, 10.0, 1.0),
    )
    model = BladeFatigueLimitState(cycles, lifetime_repetitions=50.0)
    expected_damage = 50.0 * (2.0 * 10.0**3 + 20.0**3) / 10.0**6

    assert model.damage([1.0, 3.0, 6.0]) == pytest.approx(expected_damage)
    assert model.evaluate([1.0, 3.0, 6.0]) == pytest.approx(1.0 - expected_damage)
    with pytest.raises(ValueError, match="must end with"):
        model.evaluate([1.0, 3.0])


def test_variable_contract_requires_positive_load_distribution() -> None:
    vector = build_blade_fatigue_random_vector(_settings())

    assert vector.names == ("load_factor", "sn_slope", "sn_log10_intercept")
    bad = _settings()
    bad["variables"]["load_factor"]["distribution"] = "Normal"  # type: ignore[index]
    with pytest.raises(ValueError, match="Lognormal"):
        build_blade_fatigue_random_vector(bad)


def test_form_blade_fatigue_reliability_returns_design_point() -> None:
    payload, _ = analyze_blade_fatigue_reliability(
        _solver_result(), _settings(), method="FORM"
    )

    assert payload["reference_damage"] == pytest.approx(0.61875)
    assert payload["channel_unit"] == "kN-m"
    assert payload["converged"] is True
    assert 0.0 < payload["pf"] < 0.5
    assert payload["beta"] > 0.0
    assert len(payload["design_point"]) == 3
    assert len(payload["sensitivity"]) == 3


def test_monte_carlo_uses_existing_uqra_solver() -> None:
    settings = _settings(solver_options={"n_samples": 20_000, "random_state": 71})
    payload, _ = analyze_blade_fatigue_reliability(
        _solver_result(), settings, method="Monte Carlo"
    )

    assert payload["reliability_method"] == "Monte Carlo"
    assert payload["reliability_metadata"]["backend"] == "native"
    assert payload["reliability_metadata"]["n_samples"] == 20_000
    assert payload["confidence_interval"][0] <= payload["pf"]
    assert payload["confidence_interval"][1] >= payload["pf"]


def test_configured_openfast_blade_workflow_preserves_traceability(
    tmp_path: Path,
) -> None:
    output = tmp_path / "blade.out"
    output.write_text(
        "OpenFAST v3.5.3\n"
        "Time RootMyb1\n"
        "(s) (kN-m)\n"
        "0 0\n1 10\n2 0\n3 20\n4 0\n5 15\n6 0\n",
        encoding="utf-8",
    )
    turbine = tmp_path / "turbine.yaml"
    turbine.write_text("model: reference\n", encoding="utf-8")
    project_data = {
        "schema_version": "1.0",
        "project": {"project_id": "blade-case", "name": "Blade fatigue"},
        "turbine": {
            "turbine_id": "reference-15mw",
            "model": "Reference 15 MW",
            "rated_power_mw": 15.0,
            "definition_file": str(turbine),
        },
        "solver": {
            "solver_id": "openfast-blade",
            "adapter": "openfast",
            "input_file": str(OPENFAST_INPUT),
            "output_file": str(output),
        },
        "analyses": [
            {
                "analysis_id": "blade-fatigue-form",
                "analysis_type": "blade_fatigue_reliability",
                "method": "FORM",
                "backend": "native",
                "settings": _settings(),
            }
        ],
    }
    project_file = tmp_path / "project.yaml"
    project_file.write_text(
        yaml.safe_dump(project_data, sort_keys=False), encoding="utf-8"
    )

    result = EngineeringAnalysisWorkflow(OffshoreProject.load(project_file)).run(
        "blade-fatigue-form", analyzed_at=FIXED_TIME
    )

    assert result.analysis_type == "blade_fatigue_reliability"
    assert result.payload["limit_state"] == "blade_fatigue_damage"
    assert result.payload["reliability_metadata"]["backend"] == "native"
    assert result.traceability["solver_input"]["input_file_hash"]
    assert result.traceability["solver_output"]["output_file_hash"]
    assert np.isfinite(result.payload["beta"])


def test_invalid_blade_fatigue_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="missing settings"):
        analyze_blade_fatigue_reliability(
            _solver_result(), {"channel": "blade_1_root_flap_moment"}
        )
    with pytest.raises(ValueError, match="unsupported"):
        analyze_blade_fatigue_reliability(
            _solver_result(), _settings(unknown=True), method="FORM"
        )
