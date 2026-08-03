"""Blade fatigue reliability models and analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike
from uqra import LimitStateFunction, RandomVariable, RandomVector, ReliabilityProblem

from offshoresafe.postprocessing import RainflowCycle, count_rainflow
from offshoresafe.solver import SolverResult

_VARIABLE_NAMES = ("load_factor", "sn_slope", "sn_log10_intercept")
_DISTRIBUTIONS = {
    "load_factor": "lognormal",
    "sn_slope": "normal",
    "sn_log10_intercept": "normal",
}
_SETTING_NAMES = {
    "channel",
    "lifetime_repetitions",
    "damage_limit",
    "variables",
    "correlation_matrix",
    "solver_options",
}


@dataclass(frozen=True, slots=True)
class BladeFatigueLimitState:
    """Miner fatigue margin for a repeated rainflow cycle block."""

    cycles: tuple[RainflowCycle, ...]
    lifetime_repetitions: float
    damage_limit: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "cycles", tuple(self.cycles))
        if not self.cycles:
            raise ValueError("blade fatigue limit state requires rainflow cycles")
        if not all(
            math.isfinite(cycle.range)
            and cycle.range > 0.0
            and math.isfinite(cycle.count)
            and cycle.count > 0.0
            for cycle in self.cycles
        ):
            raise ValueError(
                "rainflow cycles must have positive finite range and count"
            )
        for name in ("lifetime_repetitions", "damage_limit"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")

    def damage(self, inputs: ArrayLike) -> Any:
        """Evaluate lifetime Miner damage for one point or sample matrix."""

        values = np.asarray(inputs, dtype=float)
        if values.shape[-1:] != (3,):
            raise ValueError(
                "blade fatigue inputs must end with load factor, S-N slope, "
                "and S-N log10 intercept"
            )
        load_factor = values[..., 0]
        slope = values[..., 1]
        intercept = values[..., 2]
        if np.any(load_factor <= 0.0):
            raise ValueError("blade fatigue load factor must be positive")
        damage = np.zeros_like(load_factor, dtype=float)
        for cycle in self.cycles:
            damage = damage + cycle.count * np.power(
                load_factor * cycle.range, slope
            ) / np.power(10.0, intercept)
        return self.lifetime_repetitions * damage

    def evaluate(self, inputs: ArrayLike) -> Any:
        """Evaluate allowable damage minus accumulated lifetime damage."""

        return self.damage(inputs) * -1.0 + self.damage_limit


def _variable(name: str, definition: Any) -> RandomVariable:
    if not isinstance(definition, Mapping):
        raise TypeError(f"blade fatigue variable {name!r} must be a mapping")
    allowed = {"distribution", "parameters", "unit", "description"}
    unknown = definition.keys() - allowed
    if unknown:
        raise ValueError(f"unsupported {name} fields: {', '.join(sorted(unknown))}")
    if "distribution" not in definition or "parameters" not in definition:
        raise ValueError(
            f"blade fatigue variable {name!r} requires distribution and parameters"
        )
    distribution = str(definition["distribution"])
    if distribution.casefold() != _DISTRIBUTIONS[name]:
        expected = _DISTRIBUTIONS[name].title()
        raise ValueError(f"{name} must use the {expected} distribution")
    parameters = definition["parameters"]
    if not isinstance(parameters, Mapping) or "mean" not in parameters:
        raise ValueError(f"{name} parameters must contain an arithmetic mean")
    if name != "sn_log10_intercept" and float(parameters["mean"]) <= 0.0:
        raise ValueError(f"{name} mean must be positive")
    return RandomVariable(
        name=name,
        distribution=distribution,
        parameters=parameters,
        unit=definition.get("unit"),
        description=definition.get("description"),
    )


def build_blade_fatigue_random_vector(settings: Mapping[str, Any]) -> RandomVector:
    """Build load and S-N uncertainty variables for UQRA."""

    definitions = settings.get("variables")
    if not isinstance(definitions, Mapping):
        raise ValueError("blade fatigue reliability requires a variables mapping")
    missing = set(_VARIABLE_NAMES) - definitions.keys()
    unknown = definitions.keys() - set(_VARIABLE_NAMES)
    if missing:
        raise ValueError(
            f"missing blade fatigue variables: {', '.join(sorted(missing))}"
        )
    if unknown:
        raise ValueError(
            f"unknown blade fatigue variables: {', '.join(sorted(unknown))}"
        )
    return RandomVector(
        [_variable(name, definitions[name]) for name in _VARIABLE_NAMES],
        correlation_matrix=settings.get("correlation_matrix"),
    )


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


def analyze_blade_fatigue_reliability(
    result: SolverResult,
    settings: Mapping[str, Any],
    *,
    method: str = "FORM",
    backend: str = "native",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solve blade-root fatigue reliability from normalized load history."""

    if not isinstance(result, SolverResult):
        raise TypeError("result must be a SolverResult")
    parameters = dict(settings)
    unknown = parameters.keys() - _SETTING_NAMES
    if unknown:
        raise ValueError(
            "unsupported blade_fatigue_reliability settings: "
            f"{', '.join(sorted(unknown))}"
        )
    required = {"channel", "lifetime_repetitions", "variables"}
    missing = required - parameters.keys()
    if missing:
        raise ValueError(
            f"blade fatigue reliability missing settings: {', '.join(sorted(missing))}"
        )
    channel = str(parameters["channel"])
    try:
        values = result.channels[channel]
    except KeyError as error:
        raise KeyError(f"unknown solver channel: {channel}") from error
    cycles = count_rainflow(values).cycles
    model = BladeFatigueLimitState(
        cycles,
        lifetime_repetitions=float(parameters["lifetime_repetitions"]),
        damage_limit=float(parameters.get("damage_limit", 1.0)),
    )
    variables = build_blade_fatigue_random_vector(parameters)
    solver_options = parameters.get("solver_options", {})
    if not isinstance(solver_options, Mapping):
        raise TypeError("solver_options must be a mapping")
    reliability = ReliabilityProblem(
        variables, LimitStateFunction(model, name="blade_fatigue_damage")
    ).solve(method, backend=backend, **dict(solver_options))

    means = np.asarray(
        [float(variable.parameters["mean"]) for variable in variables.variables]
    )
    variable_payload = {
        variable.name: {
            "distribution": variable.distribution,
            "parameters": dict(variable.parameters),
            "unit": variable.unit,
        }
        for variable in variables.variables
    }
    payload = {
        "limit_state": "blade_fatigue_damage",
        "channel": channel,
        "channel_unit": result.units.get(channel),
        "cycles": [asdict(cycle) for cycle in cycles],
        "reference_damage": float(model.damage(means)),
        "lifetime_repetitions": model.lifetime_repetitions,
        "damage_limit": model.damage_limit,
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
    "BladeFatigueLimitState",
    "analyze_blade_fatigue_reliability",
    "build_blade_fatigue_random_vector",
]
