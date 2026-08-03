"""Issue #072 floating-platform reliability vertical-slice tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import yaml
from offshoresafe import (
    EngineeringAnalysisWorkflow,
    FloatingResponseLimitState,
    OffshoreProject,
    SolverResult,
    analyze_floating_reliability,
    build_floating_random_vector,
)

ROOT = Path(__file__).parents[2]
OPENFAST_INPUT = ROOT / "benchmarks/offshore/openfast_adapter/input/main.fst"
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def _settings(**updates: object) -> dict[str, object]:
    variables = {
        "significant_wave_height": {
            "distribution": "Lognormal",
            "parameters": {"mean": 6.0, "std": 0.5},
            "unit": "m",
        },
        "peak_period": {
            "distribution": "Lognormal",
            "parameters": {"mean": 10.0, "std": 0.6},
            "unit": "s",
        },
        "current_speed": {
            "distribution": "Lognormal",
            "parameters": {"mean": 1.0, "std": 0.1},
            "unit": "m/s",
        },
        "mooring_stiffness": {
            "distribution": "Lognormal",
            "parameters": {"mean": 1000.0, "std": 80.0},
            "unit": "kN/m",
        },
    }
    settings: dict[str, object] = {
        "channel": "platform_pitch",
        "response_kind": "platform_motion",
        "response_limit": 7.0,
        "reference_environment": {
            "significant_wave_height": 6.0,
            "peak_period": 10.0,
            "current_speed": 1.0,
            "mooring_stiffness": 1000.0,
        },
        "variables": variables,
    }
    settings.update(updates)
    return settings


def _result() -> SolverResult:
    return SolverResult(
        time=range(5),
        channels={"platform_pitch": [0.0, 3.0, -4.0, 2.0, 0.0]},
        units={"platform_pitch": "deg"},
        metadata={"output_file_hash": "fixture"},
    )


def test_floating_response_surface_matches_reference_state() -> None:
    model = FloatingResponseLimitState(4.0, 7.0, (6.0, 10.0, 1.0, 1000.0))
    assert model.response([6.0, 10.0, 1.0, 1000.0]) == pytest.approx(4.0)
    assert model.evaluate([6.0, 10.0, 1.0, 1000.0]) == pytest.approx(3.0)
    assert model.response([12.0, 10.0, 1.0, 1000.0]) == pytest.approx(16.0)


def test_floating_variable_order_and_positive_distributions() -> None:
    vector = build_floating_random_vector(_settings())
    assert vector.names == (
        "significant_wave_height",
        "peak_period",
        "current_speed",
        "mooring_stiffness",
    )
    bad = _settings()
    bad["variables"]["current_speed"]["distribution"] = "Normal"  # type: ignore[index]
    with pytest.raises(ValueError, match="positive"):
        build_floating_random_vector(bad)


def test_form_and_monte_carlo_return_reliability_results() -> None:
    form, _ = analyze_floating_reliability(_result(), _settings(), method="FORM")
    mc_settings = _settings(solver_options={"n_samples": 20_000, "random_state": 72})
    monte_carlo, _ = analyze_floating_reliability(
        _result(), mc_settings, method="Monte Carlo"
    )
    assert form["reference_response"] == 4.0
    assert form["converged"] is True
    assert 0.0 < form["pf"] < 0.5
    assert len(form["design_point"]) == 4
    assert monte_carlo["reliability_metadata"]["n_samples"] == 20_000
    assert monte_carlo["confidence_interval"][0] <= monte_carlo["pf"]


def test_configured_openfast_floating_workflow_preserves_traceability(
    tmp_path: Path,
) -> None:
    output = tmp_path / "floating.out"
    output.write_text(
        "OpenFAST v3.5.3\nTime PtfmPitch\n(s) (deg)\n0 0\n1 3\n2 -4\n3 2\n4 0\n",
        encoding="utf-8",
    )
    turbine = tmp_path / "turbine.yaml"
    turbine.write_text("model: floating\n", encoding="utf-8")
    data = {
        "schema_version": "1.0",
        "project": {"project_id": "floating-case", "name": "Floating reliability"},
        "turbine": {
            "turbine_id": "floating-15mw",
            "model": "Floating 15 MW",
            "rated_power_mw": 15.0,
            "definition_file": str(turbine),
        },
        "solver": {
            "solver_id": "openfast-floating",
            "adapter": "openfast",
            "input_file": str(OPENFAST_INPUT),
            "output_file": str(output),
        },
        "analyses": [
            {
                "analysis_id": "floating-form",
                "analysis_type": "floating_platform_reliability",
                "method": "FORM",
                "backend": "native",
                "settings": _settings(),
            }
        ],
    }
    project_file = tmp_path / "project.yaml"
    project_file.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    result = EngineeringAnalysisWorkflow(OffshoreProject.load(project_file)).run(
        "floating-form", analyzed_at=FIXED_TIME
    )
    assert result.payload["limit_state"] == "floating_response"
    assert result.payload["response_kind"] == "platform_motion"
    assert result.traceability["solver_output"]["output_file_hash"]
    assert np.isfinite(result.payload["beta"])


def test_invalid_floating_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="response_kind"):
        analyze_floating_reliability(_result(), _settings(response_kind="unknown"))
    with pytest.raises(ValueError, match="unsupported floating_reliability"):
        analyze_floating_reliability(_result(), _settings(unknown=True))
