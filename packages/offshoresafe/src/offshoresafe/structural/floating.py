"""Floating-platform response reliability models and analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from uqra import LimitStateFunction, RandomVariable, RandomVector, ReliabilityProblem

from offshoresafe.solver import SolverResult

_VARIABLE_NAMES = (
    "significant_wave_height",
    "peak_period",
    "current_speed",
    "mooring_stiffness",
)
_POSITIVE_DISTRIBUTIONS = {"lognormal", "weibull"}
_SETTING_NAMES = {
    "channel",
    "response_kind",
    "response_limit",
    "load_statistic",
    "reference_environment",
    "exponents",
    "variables",
    "correlation_matrix",
    "solver_options",
}


@dataclass(frozen=True, slots=True)
class FloatingResponseLimitState:
    """Screening-level motion or mooring-response safety margin."""

    reference_response: float
    response_limit: float
    reference_environment: tuple[float, float, float, float]
    exponents: tuple[float, float, float, float] = (2.0, 1.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        if not math.isfinite(self.reference_response) or self.reference_response <= 0.0:
            raise ValueError("reference_response must be finite and positive")
        if not math.isfinite(self.response_limit) or self.response_limit <= 0.0:
            raise ValueError("response_limit must be finite and positive")
        if len(self.reference_environment) != 4 or not all(
            math.isfinite(value) and value > 0.0 for value in self.reference_environment
        ):
            raise ValueError("reference_environment must contain four positive values")
        if len(self.exponents) != 4 or not all(
            math.isfinite(value) and value >= 0.0 for value in self.exponents
        ):
            raise ValueError("exponents must contain four finite non-negative values")

    def response(self, inputs: ArrayLike) -> Any:
        """Evaluate scaled motion or tension response."""

        values = np.asarray(inputs, dtype=float)
        if values.shape[-1:] != (4,):
            raise ValueError(
                "floating response inputs must end with Hs, Tp, current speed, "
                "and mooring stiffness"
            )
        if np.any(values <= 0.0):
            raise ValueError("floating response variables must be positive")
        reference = np.asarray(self.reference_environment)
        ratios = values / reference
        environmental = (
            np.power(ratios[..., 0], self.exponents[0])
            * np.power(ratios[..., 1], self.exponents[1])
            * np.power(ratios[..., 2], self.exponents[2])
            * np.power(1.0 / ratios[..., 3], self.exponents[3])
        )
        return self.reference_response * environmental

    def evaluate(self, inputs: ArrayLike) -> Any:
        """Evaluate response limit minus predicted response."""

        return self.response_limit - self.response(inputs)


def _variable(name: str, definition: Any) -> RandomVariable:
    if not isinstance(definition, Mapping):
        raise TypeError(f"floating variable {name!r} must be a mapping")
    allowed = {"distribution", "parameters", "unit", "description"}
    unknown = definition.keys() - allowed
    if unknown:
        raise ValueError(f"unsupported {name} fields: {', '.join(sorted(unknown))}")
    if "distribution" not in definition or "parameters" not in definition:
        raise ValueError(
            f"floating variable {name!r} requires distribution and parameters"
        )
    distribution = str(definition["distribution"])
    if distribution.casefold() not in _POSITIVE_DISTRIBUTIONS:
        raise ValueError(
            f"{name} must use a positive Lognormal or Weibull distribution"
        )
    return RandomVariable(
        name=name,
        distribution=distribution,
        parameters=definition["parameters"],
        unit=definition.get("unit"),
        description=definition.get("description"),
    )


def build_floating_random_vector(settings: Mapping[str, Any]) -> RandomVector:
    """Build Hs, Tp, current, and mooring-stiffness UQRA variables."""

    definitions = settings.get("variables")
    if not isinstance(definitions, Mapping):
        raise ValueError("floating reliability requires a variables mapping")
    missing = set(_VARIABLE_NAMES) - definitions.keys()
    unknown = definitions.keys() - set(_VARIABLE_NAMES)
    if missing:
        raise ValueError(f"missing floating variables: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"unknown floating variables: {', '.join(sorted(unknown))}")
    return RandomVector(
        [_variable(name, definitions[name]) for name in _VARIABLE_NAMES],
        correlation_matrix=settings.get("correlation_matrix"),
    )


def _named_values(
    values: Any, *, name: str, defaults: Mapping[str, float] | None = None
) -> tuple[float, float, float, float]:
    if values is None and defaults is not None:
        values = defaults
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a mapping")
    missing = set(_VARIABLE_NAMES) - values.keys()
    unknown = values.keys() - set(_VARIABLE_NAMES)
    if missing or unknown:
        raise ValueError(f"{name} must define exactly {', '.join(_VARIABLE_NAMES)}")
    return tuple(float(values[key]) for key in _VARIABLE_NAMES)  # type: ignore[return-value]


def _reference_response(result: SolverResult, channel: str, statistic: str) -> float:
    try:
        values = result.channels[channel]
    except KeyError as error:
        raise KeyError(f"unknown solver channel: {channel}") from error
    key = statistic.casefold().replace("-", "_")
    if key == "maximum":
        response = max(values)
    elif key == "minimum":
        response = abs(min(values))
    elif key in {"maximum_absolute", "absolute_maximum"}:
        response = max(abs(value) for value in values)
    else:
        raise ValueError(
            "load_statistic must be 'maximum', 'minimum', or 'maximum_absolute'"
        )
    if response <= 0.0:
        raise ValueError("selected floating reference response must be positive")
    return response


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def analyze_floating_reliability(
    result: SolverResult,
    settings: Mapping[str, Any],
    *,
    method: str = "FORM",
    backend: str = "native",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solve screening-level floating response reliability."""

    if not isinstance(result, SolverResult):
        raise TypeError("result must be a SolverResult")
    parameters = dict(settings)
    unknown = parameters.keys() - _SETTING_NAMES
    if unknown:
        raise ValueError(
            f"unsupported floating_reliability settings: {', '.join(sorted(unknown))}"
        )
    required = {
        "channel",
        "response_kind",
        "response_limit",
        "reference_environment",
        "variables",
    }
    missing = required - parameters.keys()
    if missing:
        raise ValueError(
            f"floating reliability missing settings: {', '.join(sorted(missing))}"
        )
    response_kind = str(parameters["response_kind"]).casefold().replace("-", "_")
    if response_kind not in {"platform_motion", "mooring_tension"}:
        raise ValueError("response_kind must be 'platform_motion' or 'mooring_tension'")
    channel = str(parameters["channel"])
    statistic = str(parameters.get("load_statistic", "maximum_absolute"))
    reference_response = _reference_response(result, channel, statistic)
    reference_environment = _named_values(
        parameters["reference_environment"], name="reference_environment"
    )
    exponents = _named_values(
        parameters.get("exponents"),
        name="exponents",
        defaults={
            "significant_wave_height": 2.0,
            "peak_period": 1.0,
            "current_speed": 1.0,
            "mooring_stiffness": 1.0,
        },
    )
    model = FloatingResponseLimitState(
        reference_response=reference_response,
        response_limit=float(parameters["response_limit"]),
        reference_environment=reference_environment,
        exponents=exponents,
    )
    variables = build_floating_random_vector(parameters)
    solver_options = parameters.get("solver_options", {})
    if not isinstance(solver_options, Mapping):
        raise TypeError("solver_options must be a mapping")
    reliability = ReliabilityProblem(
        variables, LimitStateFunction(model, name="floating_response")
    ).solve(method, backend=backend, **dict(solver_options))
    variable_payload = {
        variable.name: {
            "distribution": variable.distribution,
            "parameters": dict(variable.parameters),
            "unit": variable.unit,
        }
        for variable in variables.variables
    }
    payload = {
        "limit_state": "floating_response",
        "response_kind": response_kind,
        "channel": channel,
        "channel_unit": result.units.get(channel),
        "load_statistic": statistic,
        "reference_response": reference_response,
        "response_limit": model.response_limit,
        "reference_environment": dict(zip(_VARIABLE_NAMES, reference_environment)),
        "exponents": dict(zip(_VARIABLE_NAMES, exponents)),
        "variables": variable_payload,
        "correlation_matrix": variables.correlation_matrix.tolist(),
        "pf": reliability.pf,
        "beta": reliability.beta,
        "confidence_interval": _json_value(reliability.confidence_interval),
        "design_point": _json_value(reliability.design_point),
        "standard_normal_design_point": _json_value(
            reliability.standard_normal_design_point
        ),
        "sensitivity": _json_value(reliability.sensitivity),
        "converged": reliability.converged,
        "iterations": reliability.iterations,
        "reliability_method": reliability.method,
        "reliability_metadata": _json_value(reliability.metadata),
    }
    return payload, parameters


__all__ = [
    "FloatingResponseLimitState",
    "analyze_floating_reliability",
    "build_floating_random_vector",
]
