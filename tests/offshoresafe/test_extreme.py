"""Issue #061 extreme-response tests."""

from __future__ import annotations

import math

import pytest
from offshoresafe import (
    SolverResult,
    extract_peaks,
    fit_extreme_distribution,
    return_period_response,
)


def test_peak_extraction_preserves_time_unit_and_traceability() -> None:
    source = SolverResult(
        time=range(9),
        channels={"load": [0, 3, 1, 5, 0, 4, 1, 2, 0]},
        units={"load": "kN"},
        metadata={"output_file_hash": "abc"},
    )
    peaks = extract_peaks(source, "load", threshold=3.5, min_distance=2)

    assert [(peak.index, peak.time, peak.value) for peak in peaks.peaks] == [
        (3, 3.0, 5.0),
        (5, 5.0, 4.0),
    ]
    assert peaks.unit == "kN"
    assert peaks.metadata["output_file_hash"] == "abc"
    assert peaks.metadata["processing_method"] == "peak_extraction"


def test_minima_and_absolute_peak_directions() -> None:
    source = SolverResult(time=range(5), channels={"load": [0, -4, 1, -2, 0]})
    assert extract_peaks(source, "load", direction="minima").values == (-4.0, -2.0)
    assert extract_peaks(source, "load", direction="absolute").values == (-4.0, -2.0)


def test_gumbel_fit_and_return_period_response() -> None:
    values = [8.2, 9.1, 10.4, 8.9, 11.3, 9.8]
    fitted = fit_extreme_distribution(values)
    response = return_period_response(fitted, 50.0, events_per_period=12.0)

    assert fitted.distribution == "gumbel"
    assert fitted.sample_count == len(values)
    assert fitted.parameters["scale"] > 0.0
    assert math.isfinite(response)
    assert response > max(values)


def test_weibull_fit_and_invalid_inputs() -> None:
    fitted = fit_extreme_distribution([1.0, 2.0, 3.0], distribution="weibull")
    assert fitted.quantile(0.9) > 0.0
    with pytest.raises(ValueError, match="strictly positive"):
        fit_extreme_distribution([0.0, 1.0], distribution="weibull")
    with pytest.raises(ValueError, match="return_period"):
        return_period_response(fitted, 1.0)


def test_peak_validation() -> None:
    source = SolverResult(time=[0, 1, 2], channels={"load": [0, 1, 0]})
    with pytest.raises(KeyError, match="missing"):
        extract_peaks(source, "missing")
    with pytest.raises(ValueError, match="positive integer"):
        extract_peaks(source, "load", min_distance=0)
    with pytest.raises(ValueError, match="no peaks"):
        extract_peaks(source, "load", threshold=2.0)
