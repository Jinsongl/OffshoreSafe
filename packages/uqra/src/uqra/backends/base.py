"""Backend contracts and capability identifiers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class Capability(StrEnum):
    """Algorithms discoverable through the backend interface."""

    DISTRIBUTION_NORMAL = "distribution.normal"
    DISTRIBUTION_LOGNORMAL = "distribution.lognormal"
    DISTRIBUTION_WEIBULL = "distribution.weibull"
    DISTRIBUTION_UNIFORM = "distribution.uniform"
    RELIABILITY_MONTE_CARLO = "reliability.monte_carlo"
    RELIABILITY_FORM = "reliability.form"
    RELIABILITY_SORM = "reliability.sorm"
    SAMPLING_MONTE_CARLO = "sampling.monte_carlo"
    SAMPLING_LATIN_HYPERCUBE = "sampling.latin_hypercube"
    SAMPLING_SOBOL = "sampling.sobol"
    SENSITIVITY_SOBOL = "sensitivity.sobol"
    SENSITIVITY_MORRIS = "sensitivity.morris"
    SURROGATE_PCE = "surrogate.pce"


def normalize_capability(capability: Capability | str) -> Capability:
    """Convert a public string identifier to a validated capability."""
    if isinstance(capability, Capability):
        return capability
    try:
        return Capability(str(capability).casefold().replace("-", "_"))
    except ValueError as error:
        raise ValueError(f"unknown backend capability: {capability!r}") from error


class Backend(ABC):
    """Common metadata and discovery contract for optional backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable backend identifier."""

    @property
    @abstractmethod
    def capabilities(self) -> frozenset[Capability]:
        """Return algorithms implemented by this backend."""

    def supports(self, capability: Capability | str) -> bool:
        """Report whether the backend implements a capability."""
        return normalize_capability(capability) in self.capabilities


class ReliabilityBackend(Backend):
    """Contract for reliability algorithm providers."""

    @abstractmethod
    def solve_reliability(self, problem: Any, method: str, **options: Any) -> Any:
        """Solve a reliability problem and return a normalizable result."""


class SamplingBackend(Backend):
    """Contract for unit-hypercube sampling providers."""

    @abstractmethod
    def sample(
        self,
        method: str,
        dimension: int,
        n_samples: int,
        *,
        random_state: Any = None,
        **options: Any,
    ) -> Any:
        """Generate samples and return a normalizable result."""


class SensitivityBackend(Backend):
    """Contract for global sensitivity algorithm providers."""

    @abstractmethod
    def analyze_sensitivity(self, model: Any, method: str, **options: Any) -> Any:
        """Analyze a model and return a normalizable result."""


class SurrogateBackend(Backend):
    """Contract for surrogate-model providers."""

    @abstractmethod
    def fit_surrogate(
        self, model: Any, variables: Any, method: str, **options: Any
    ) -> Any:
        """Fit a surrogate and return a normalizable result."""


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    """Backend-independent sensitivity result."""

    method: str
    indices: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.method:
            raise ValueError("method must be a non-empty string")
        object.__setattr__(self, "indices", MappingProxyType(dict(self.indices)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class SurrogateResult:
    """Backend-independent fitted surrogate with summary statistics."""

    method: str
    surrogate: Any
    statistics: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.method, str) or not self.method.strip():
            raise ValueError("method must be a non-empty string")
        if not callable(self.surrogate):
            raise TypeError("surrogate must be callable")
        object.__setattr__(self, "statistics", MappingProxyType(dict(self.statistics)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def predict(self, samples: Any) -> Any:
        """Evaluate the fitted surrogate at one point or a row-wise sample matrix."""
        return self.surrogate(samples)


__all__ = [
    "Backend",
    "Capability",
    "ReliabilityBackend",
    "SamplingBackend",
    "SensitivityBackend",
    "SensitivityResult",
    "SurrogateBackend",
    "SurrogateResult",
    "normalize_capability",
]
