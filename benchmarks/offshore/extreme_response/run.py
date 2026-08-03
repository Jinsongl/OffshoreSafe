"""Deterministic Issue #061 extreme-response benchmark."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import (  # noqa: E402
    SolverResult,
    extract_peaks,
    fit_extreme_distribution,
    return_period_response,
)


def main() -> None:
    source = SolverResult(
        time=range(11),
        channels={"load": [0, 8, 0, 10, 0, 9, 0, 12, 0, 11, 0]},
        units={"load": "kN"},
    )
    peaks = extract_peaks(source, "load")
    fitted = fit_extreme_distribution(peaks)
    response = return_period_response(fitted, 50.0)
    expected = fitted.quantile(0.98)
    assert peaks.values == (8.0, 10.0, 9.0, 12.0, 11.0)
    assert math.isclose(response, expected, abs_tol=1e-12)
    print("extreme-response benchmark passed")


if __name__ == "__main__":
    main()
