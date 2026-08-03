"""Tower-base bending reliability models and analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from uqra import LimitStateFunction, RandomVariable, RandomVector, ReliabilityProblem

from offshoresafe.solver import SolverResult

_VARIABLE_NAMES = ("yield_strength", "section_modulus", "load_factor")
_SETTING_NAMES = {
    "channel",
    "load_statistic",
    "variables",
    "correlation_matrix",
    "material_factor",
    "load_factor_design",
    "solver_options",
}


@dataclass(frozen=True, slots=True)
class TowerBendingLimitState:
    """Tower bending safety margin in kN-m.

    Input columns are yield strength in MPa, section modulus in ``m^3``, and a
    dimensionless stochastic load factor, in that order.
    """

    reference_moment: float
    material_factor: float = 1.0
    load_factor_design: float = 1.0

    def __post_init__(self) -> None:
        for name in ("reference_moment", "material_factor", "load_factor_design"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")

    def evaluate(self, inputs: ArrayLike) -> Any:
        """Evaluate capacity minus factored tower-base bending moment."""

        values = np.asarray(inputs, dtype=float)
        if values.shape[-1:] != (3,):
            raise ValueError(
                "tower bending inputs must end with yield strength, "
                "section modulus, and load factor"
            )
        capacity = values[..., 0] * values[..., 1] * 1000.0 / self.material_factor
        demand = self.reference_moment * values[..., 2] * self.load_factor_design
        return capacity - demand


def _variable(name: str, definition: Any) -> RandomVariable:
    if not isinstance(definition, Mapping):
        raise TypeError(f"tower variable {name!r} must be a mapping")
    allowed = {"distribution", "parameters", "unit", "description"}
    unknown = definition.keys() - allowed
    if unknown:
        raise ValueError(f"unsupported {name} fields: {', '.join(sorted(unknown))}")
    if "distribution" not in definition or "parameters" not in definition:
        raise ValueError(
            f"tower variable {name!r} requires distribution and parameters"
        )
    return RandomVariable(
        name=name,
        distribution=str(definition["distribution"]),
        parameters=definition["parameters"],
        unit=definition.get("unit"),
        description=definition.get("description"),
    )


def build_tower_random_vector(settings: Mapping[str, Any]) -> RandomVector:
    """Build the domain-independent UQRA variable vector from tower settings."""

    definitions = settings.get("variables")
    if not isinstance(definitions, Mapping):
        raise ValueError("tower reliability requires a variables mapping")
    missing = set(_VARIABLE_NAMES) - definitions.keys()
    unknown = definitions.keys() - set(_VARIABLE_NAMES)
    if missing:
        raise ValueError(f"missing tower variables: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"unknown tower variables: {', '.join(sorted(unknown))}")
    variables = [_variable(name, definitions[name]) for name in _VARIABLE_NAMES]
    return RandomVector(
        variables,
        correlation_matrix=settings.get("correlation_matrix"),
    )


def _reference_moment(result: SolverResult, channel: str, statistic: str) -> float:
    try:
        values = result.channels[channel]
    except KeyError as error:
        raise KeyError(f"unknown solver channel: {channel}") from error
    key = statistic.casefold().replace("-", "_")
    if key == "maximum":
        reference = max(values)
    elif key == "minimum":
        reference = abs(min(values))
    elif key in {"maximum_absolute", "absolute_maximum"}:
        reference = max(abs(value) for value in values)
    else:
        raise ValueError(
            "load_statistic must be 'maximum', 'minimum', or 'maximum_absolute'"
        )
    if reference <= 0.0:
        raise ValueError("selected tower reference moment must be positive")
    return reference


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


def analyze_tower_reliability(
    result: SolverResult,
    settings: Mapping[str, Any],
    *,
    method: str = "FORM",
    backend: str = "native",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solve tower-base bending reliability using normalized solver loads."""

    if not isinstance(result, SolverResult):
        raise TypeError("result must be a SolverResult")
    parameters = dict(settings)
    unknown = parameters.keys() - _SETTING_NAMES
    if unknown:
        raise ValueError(
            f"unsupported tower_reliability settings: {', '.join(sorted(unknown))}"
        )
    if "channel" not in parameters:
        raise ValueError("tower reliability requires a channel setting")
    channel = str(parameters["channel"])
    statistic = str(parameters.get("load_statistic", "maximum_absolute"))
    reference = _reference_moment(result, channel, statistic)
    material_factor = float(parameters.get("material_factor", 1.0))
    load_factor_design = float(parameters.get("load_factor_design", 1.0))
    model = TowerBendingLimitState(
        reference,
        material_factor=material_factor,
        load_factor_design=load_factor_design,
    )
    variables = build_tower_random_vector(parameters)
    solver_options = parameters.get("solver_options", {})
    if not isinstance(solver_options, Mapping):
        raise TypeError("solver_options must be a mapping")
    reliability = ReliabilityProblem(
        variables, LimitStateFunction(model, name="tower_base_bending")
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
        "limit_state": "tower_base_bending",
        "channel": channel,
        "channel_unit": result.units.get(channel),
        "load_statistic": statistic,
        "reference_moment": reference,
        "material_factor": material_factor,
        "load_factor_design": load_factor_design,
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
    "TowerBendingLimitState",
    "analyze_tower_reliability",
    "build_tower_random_vector",
]
