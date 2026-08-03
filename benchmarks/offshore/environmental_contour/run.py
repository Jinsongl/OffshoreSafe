"""Deterministic Issues #080/#081 Hs-Tp IFORM benchmark."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import MetoceanModel  # noqa: E402


def main() -> None:
    model = MetoceanModel.from_config(
        {
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
    )
    contour = model.iform_contour(50.0, events_per_period=365.25, n_points=72)
    expected_probability = 1.0 / (50.0 * 365.25)
    expected_beta = stats.norm.ppf(1.0 - expected_probability)

    assert math.isclose(contour.beta, expected_beta, rel_tol=1.0e-12)
    assert np.allclose(
        np.linalg.norm(contour.standard_normal_points, axis=1), expected_beta
    )
    assert np.all(np.asarray(contour.points) > 0.0)
    assert math.isclose(contour.points[0][0], 9.276538184146425, rel_tol=1.0e-10)
    assert contour.variable_names == ("significant_wave_height", "peak_period")
    print("Hs-Tp IFORM environmental contour benchmark passed")


if __name__ == "__main__":
    main()
