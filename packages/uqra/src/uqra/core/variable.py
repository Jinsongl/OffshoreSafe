"""Random-variable data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class RandomVariable:
    """Describe one uncertain scalar quantity.

    Distribution-specific behavior is provided separately by the
    distribution interface. This object stores only the stable,
    backend-independent definition of a random variable.

    Args:
        name: Unique, non-empty variable name.
        distribution: Non-empty distribution identifier, such as ``"Normal"``.
        parameters: Distribution parameter names and values.
        unit: Optional physical unit.
        description: Optional human-readable description.
    """

    name: str
    distribution: str
    parameters: dict[str, Any] = field(default_factory=dict)
    unit: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate identifiers and detach parameters from caller-owned data."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.distribution, str) or not self.distribution.strip():
            raise ValueError("distribution must be a non-empty string")
        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")
        if self.unit is not None and not isinstance(self.unit, str):
            raise TypeError("unit must be a string or None")
        if self.description is not None and not isinstance(self.description, str):
            raise TypeError("description must be a string or None")

        self.name = self.name.strip()
        self.distribution = self.distribution.strip()
        self.parameters = dict(self.parameters)
