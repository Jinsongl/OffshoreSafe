"""Normalize optional backend outputs into UQRA result objects."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from uqra.backends.base import SensitivityResult, SurrogateResult
from uqra.reliability import ReliabilityResult
from uqra.sampling import SamplingResult


def _required(data: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in data:
            return data[name]
    raise ValueError(f"backend result is missing required field {names[0]!r}")


def normalize_reliability_result(result: Any) -> ReliabilityResult:
    """Normalize a native result or a mapping returned by a plugin."""
    if isinstance(result, ReliabilityResult):
        return result
    if not isinstance(result, Mapping):
        raise TypeError("reliability backend result must be a mapping")
    return ReliabilityResult(
        pf=float(_required(result, "pf", "Pf", "failure_probability")),
        beta=float(_required(result, "beta", "reliability_index")),
        method=str(_required(result, "method")),
        confidence_interval=result.get("confidence_interval"),
        design_point=result.get("design_point"),
        standard_normal_design_point=result.get("standard_normal_design_point"),
        sensitivity=result.get("sensitivity"),
        converged=result.get("converged"),
        iterations=result.get("iterations"),
        metadata=dict(result.get("metadata", {})),
    )


def normalize_sampling_result(result: Any) -> SamplingResult:
    """Normalize a native result or a mapping returned by a plugin."""
    if isinstance(result, SamplingResult):
        return result
    if not isinstance(result, Mapping):
        raise TypeError("sampling backend result must be a mapping")
    return SamplingResult(
        samples=_required(result, "samples"),
        metadata=dict(result.get("metadata", {})),
    )


def normalize_sensitivity_result(result: Any) -> SensitivityResult:
    """Normalize a native result or a mapping returned by a plugin."""
    if isinstance(result, SensitivityResult):
        return result
    if not isinstance(result, Mapping):
        raise TypeError("sensitivity backend result must be a mapping")
    return SensitivityResult(
        method=str(_required(result, "method")),
        indices=_required(result, "indices"),
        metadata=dict(result.get("metadata", {})),
    )


def normalize_surrogate_result(result: Any) -> SurrogateResult:
    """Normalize a fitted surrogate object or plugin result mapping."""
    if isinstance(result, SurrogateResult):
        return result
    if not isinstance(result, Mapping):
        raise TypeError("surrogate backend result must be a mapping")
    return SurrogateResult(
        method=str(_required(result, "method")),
        surrogate=_required(result, "surrogate", "predictor", "model"),
        statistics=dict(result.get("statistics", {})),
        metadata=dict(result.get("metadata", {})),
    )


__all__ = [
    "normalize_reliability_result",
    "normalize_sampling_result",
    "normalize_sensitivity_result",
    "normalize_surrogate_result",
]
