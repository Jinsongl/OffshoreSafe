"""Issue #070 tower reliability vertical-slice tests."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest
import yaml
from offshoresafe import (
    EngineeringAnalysisWorkflow,
    OffshoreProject,
    SolverResult,
    TowerBendingLimitState,
    analyze_tower_reliability,
    build_tower_random_vector,
)

ROOT = Path(__file__).parents[2]
OPENFAST_INPUT = (
    ROOT / "benchmarks" / "offshore" / "openfast_adapter" / "input" / "main.fst"
)
FIXED_TIME = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def _settings(**updates: object) -> dict[str, object]:
    settings: dict[str, object] = {
        "channel": "tower_base_fore_aft_moment",
        "load_statistic": "maximum_absolute",
        "variables": {
            "yield_strength": {
                "distribution": "Normal",
                "parameters": {"mean": 355.0, "std": 17.75},
                "unit": "MPa",
            },
            "section_modulus": {
                "distribution": "Normal",
                "parameters": {"mean": 0.1, "std": 0.005},
                "unit": "m^3",
            },
            "load_factor": {
                "distribution": "Normal",
                "parameters": {"mean": 1.0, "std": 0.05},
                "unit": None,
            },
        },
    }
    settings.update(updates)
    return settings


def _solver_result() -> SolverResult:
    return SolverResult(
        time=[0.0, 1.0, 2.0, 3.0, 4.0],
        channels={
            "tower_base_fore_aft_moment": [0.0, 20_000.0, -25_000.0, 15_000.0, 0.0]
        },
        units={"tower_base_fore_aft_moment": "kN-m"},
        metadata={"output_file_hash": "fixture-hash"},
    )


def test_tower_bending_limit_state_formula_and_shapes() -> None:
    model = TowerBendingLimitState(25_000.0)

    assert model.evaluate([355.0, 0.1, 1.0]) == pytest.approx(10_500.0)
    assert model.evaluate([[355.0, 0.1, 1.0], [250.0, 0.1, 1.0]]) == pytest.approx(
        [10_500.0, 0.0]
    )
    with pytest.raises(ValueError, match="must end with"):
        model.evaluate([355.0, 0.1])


def test_variable_contract_preserves_material_geometry_and_load_order() -> None:
    vector = build_tower_random_vector(_settings())

    assert vector.names == ("yield_strength", "section_modulus", "load_factor")
    assert vector.variables[0].unit == "MPa"
    with pytest.raises(ValueError, match="missing tower variables"):
        build_tower_random_vector({"variables": {}})


def test_form_tower_reliability_matches_first_order_reference() -> None:
    payload, _ = analyze_tower_reliability(_solver_result(), _settings(), method="FORM")

    mean_margin = 355.0 * 0.1 * 1000.0 - 25_000.0
    linearized_std = math.sqrt(
        (0.1 * 1000.0 * 17.75) ** 2
        + (355.0 * 1000.0 * 0.005) ** 2
        + (25_000.0 * 0.05) ** 2
    )
    first_order_beta = mean_margin / linearized_std

    assert payload["reference_moment"] == 25_000.0
    assert payload["channel_unit"] == "kN-m"
    assert payload["converged"] is True
    # The analytical value linearizes the multiplicative resistance at its mean.
    assert payload["beta"] == pytest.approx(first_order_beta, rel=0.06)
    assert 0.0 < payload["pf"] < 1.0e-3
    assert len(payload["design_point"]) == 3
    assert len(payload["sensitivity"]) == 3


def test_monte_carlo_uses_existing_uqra_solver() -> None:
    settings = _settings(solver_options={"n_samples": 20_000, "random_state": 70})
    payload, _ = analyze_tower_reliability(
        _solver_result(), settings, method="Monte Carlo"
    )

    assert payload["reliability_method"] == "Monte Carlo"
    assert payload["reliability_metadata"]["backend"] == "native"
    assert payload["reliability_metadata"]["n_samples"] == 20_000
    assert payload["confidence_interval"][0] <= payload["pf"]
    assert payload["confidence_interval"][1] >= payload["pf"]


def test_configured_openfast_tower_workflow_preserves_traceability(
    tmp_path: Path,
) -> None:
    output = tmp_path / "tower.out"
    output.write_text(
        "OpenFAST v3.5.3\n"
        "Time TwrBsMyt\n"
        "(s) (kN-m)\n"
        "0 0\n1 20000\n2 -25000\n3 15000\n4 0\n",
        encoding="utf-8",
    )
    turbine = tmp_path / "turbine.yaml"
    turbine.write_text("model: reference\n", encoding="utf-8")
    project_data = {
        "schema_version": "1.0",
        "project": {"project_id": "tower-case", "name": "Tower reliability"},
        "turbine": {
            "turbine_id": "reference-15mw",
            "model": "Reference 15 MW",
            "rated_power_mw": 15.0,
            "definition_file": str(turbine),
        },
        "solver": {
            "solver_id": "openfast-tower",
            "adapter": "openfast",
            "input_file": str(OPENFAST_INPUT),
            "output_file": str(output),
        },
        "analyses": [
            {
                "analysis_id": "tower-form",
                "analysis_type": "tower_reliability",
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
        "tower-form", analyzed_at=FIXED_TIME
    )

    assert result.analysis_type == "tower_reliability"
    assert result.payload["limit_state"] == "tower_base_bending"
    assert result.payload["reliability_metadata"]["backend"] == "native"
    assert result.traceability["solver_input"]["input_file_hash"]
    assert result.traceability["solver_output"]["output_file_hash"]
    assert np.isfinite(result.payload["beta"])


def test_invalid_tower_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="load_statistic"):
        analyze_tower_reliability(
            _solver_result(), _settings(load_statistic="rms"), method="FORM"
        )
    with pytest.raises(ValueError, match="unsupported tower_reliability settings"):
        analyze_tower_reliability(
            _solver_result(), _settings(unknown=True), method="FORM"
        )
