"""Issues #080 and #081 metocean model and contour tests."""

from __future__ import annotations

import numpy as np
import pytest
from offshoresafe import MetoceanModel


def _config() -> dict[str, object]:
    return {
        "variables": {
            "significant_wave_height": {
                "distribution": "Weibull",
                "parameters": {"scale": 3.0, "shape": 2.0},
                "unit": "m",
            },
            "peak_period": {
                "distribution": "Lognormal",
                "parameters": {"mean": 9.0, "std": 1.2},
                "unit": "s",
            },
        },
        "correlation_matrix": [[1.0, 0.35], [0.35, 1.0]],
    }


def test_metocean_model_preserves_names_units_and_dependence() -> None:
    model = MetoceanModel.from_config(_config())

    assert model.variables.names == ("significant_wave_height", "peak_period")
    assert model.units == {"significant_wave_height": "m", "peak_period": "s"}
    assert np.allclose(model.variables.correlation_matrix, [[1.0, 0.35], [0.35, 1.0]])


def test_hs_tp_contour_is_positive_named_and_immutable() -> None:
    contour = MetoceanModel.from_config(_config()).iform_contour(
        50.0, events_per_period=365.25, n_points=72
    )

    points = np.asarray(contour.points)
    assert points.shape == (72, 2)
    assert np.all(points > 0.0)
    assert np.linalg.norm(contour.standard_normal_points, axis=1) == pytest.approx(
        contour.beta
    )
    assert contour.metadata["processing_method"] == "iform_environmental_contour"
    assert contour.as_records()[0].keys() == {
        "significant_wave_height",
        "peak_period",
    }
    with pytest.raises(TypeError):
        contour.units["peak_period"] = "changed"  # type: ignore[index]


def test_wind_wave_current_model_supports_explicit_surface_directions() -> None:
    config = _config()
    config["variables"]["wind_speed"] = {  # type: ignore[index]
        "distribution": "Weibull",
        "parameters": {"scale": 10.0, "shape": 2.1},
        "unit": "m/s",
    }
    config["correlation_matrix"] = [
        [1.0, 0.35, 0.2],
        [0.35, 1.0, 0.1],
        [0.2, 0.1, 1.0],
    ]
    contour = MetoceanModel.from_config(config).iform_contour(
        50.0, directions=[[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    )
    assert contour.variable_names == (
        "significant_wave_height",
        "peak_period",
        "wind_speed",
    )
    assert len(contour.points) == 3


def test_invalid_metocean_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least two"):
        MetoceanModel.from_config({"variables": {}})
    bad = _config()
    bad["variables"]["temperature"] = {  # type: ignore[index]
        "distribution": "Normal",
        "parameters": {"mean": 10.0, "std": 1.0},
    }
    with pytest.raises(ValueError, match="unsupported metocean variable"):
        MetoceanModel.from_config(bad)
