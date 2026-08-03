"""Offshore metocean random models and environmental contours."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import numpy as np
from uqra import IFORMContour, RandomVariable, RandomVector

SUPPORTED_METOCEAN_VARIABLES = frozenset(
    {
        "significant_wave_height",
        "peak_period",
        "wind_speed",
        "current_speed",
        "wave_direction",
        "wind_direction",
        "current_direction",
    }
)


@dataclass(frozen=True, slots=True)
class EnvironmentalContourResult:
    """Immutable engineering names, units, and physical IFORM points."""

    variable_names: tuple[str, ...]
    units: Mapping[str, str | None]
    points: tuple[tuple[float, ...], ...]
    standard_normal_points: tuple[tuple[float, ...], ...]
    beta: float
    exceedance_probability: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.variable_names) < 2 or len(set(self.variable_names)) != len(
            self.variable_names
        ):
            raise ValueError(
                "contour variable names must be unique and have dimension >= 2"
            )
        points = tuple(tuple(float(value) for value in row) for row in self.points)
        standard = tuple(
            tuple(float(value) for value in row) for row in self.standard_normal_points
        )
        if not points or len(points) != len(standard):
            raise ValueError("physical and standard-normal contours must align")
        if any(len(row) != len(self.variable_names) for row in (*points, *standard)):
            raise ValueError("contour point dimension must match variable names")
        if not all(
            math.isfinite(value) for row in (*points, *standard) for value in row
        ):
            raise ValueError("contour points must be finite")
        object.__setattr__(self, "points", points)
        object.__setattr__(self, "standard_normal_points", standard)
        object.__setattr__(self, "units", MappingProxyType(dict(self.units)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def as_records(self) -> tuple[Mapping[str, float], ...]:
        """Return physical contour points keyed by engineering variable name."""

        return tuple(
            MappingProxyType(dict(zip(self.variable_names, row))) for row in self.points
        )


class MetoceanModel:
    """Named metocean marginals and Gaussian-copula dependence."""

    def __init__(self, variables: RandomVector) -> None:
        if not isinstance(variables, RandomVector):
            raise TypeError("variables must be a RandomVector")
        unsupported = set(variables.names) - SUPPORTED_METOCEAN_VARIABLES
        if unsupported:
            raise ValueError(
                f"unsupported metocean variables: {', '.join(sorted(unsupported))}"
            )
        if variables.dimension < 2:
            raise ValueError("metocean models require at least two variables")
        self.variables = variables
        self.units = MappingProxyType(
            {variable.name: variable.unit for variable in variables.variables}
        )

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> MetoceanModel:
        """Build a strict metocean model from a JSON/YAML-compatible mapping."""

        if not isinstance(config, Mapping):
            raise TypeError("metocean config must be a mapping")
        unknown_root = config.keys() - {"variables", "correlation_matrix"}
        if unknown_root:
            raise ValueError(
                f"unsupported metocean settings: {', '.join(sorted(unknown_root))}"
            )
        definitions = config.get("variables")
        if not isinstance(definitions, Mapping) or len(definitions) < 2:
            raise ValueError(
                "metocean variables must be a mapping with at least two entries"
            )
        variables: list[RandomVariable] = []
        for name, definition in definitions.items():
            if name not in SUPPORTED_METOCEAN_VARIABLES:
                raise ValueError(f"unsupported metocean variable: {name}")
            if not isinstance(definition, Mapping):
                raise TypeError(f"metocean variable {name!r} must be a mapping")
            unknown = definition.keys() - {
                "distribution",
                "parameters",
                "unit",
                "description",
            }
            if unknown:
                raise ValueError(
                    f"unsupported {name} fields: {', '.join(sorted(unknown))}"
                )
            if "distribution" not in definition or "parameters" not in definition:
                raise ValueError(f"{name} requires distribution and parameters")
            variables.append(
                RandomVariable(
                    name=name,
                    distribution=str(definition["distribution"]),
                    parameters=definition["parameters"],
                    unit=definition.get("unit"),
                    description=definition.get("description"),
                )
            )
        return cls(
            RandomVector(
                variables,
                correlation_matrix=config.get("correlation_matrix"),
            )
        )

    def iform_contour(
        self,
        return_period: float,
        *,
        events_per_period: float = 1.0,
        n_points: int = 360,
        directions: Any = None,
    ) -> EnvironmentalContourResult:
        """Generate a named physical IFORM contour."""

        contour = IFORMContour(self.variables).generate(
            return_period,
            events_per_period=events_per_period,
            n_points=n_points,
            directions=directions,
        )
        return EnvironmentalContourResult(
            variable_names=self.variables.names,
            units=self.units,
            points=tuple(map(tuple, contour.physical_points.tolist())),
            standard_normal_points=tuple(
                map(tuple, contour.standard_normal_points.tolist())
            ),
            beta=contour.beta,
            exceedance_probability=contour.exceedance_probability,
            metadata={
                **dict(contour.metadata),
                "processing_method": "iform_environmental_contour",
                "correlation_matrix": np.asarray(
                    self.variables.correlation_matrix
                ).tolist(),
            },
        )


__all__ = [
    "SUPPORTED_METOCEAN_VARIABLES",
    "EnvironmentalContourResult",
    "MetoceanModel",
]
