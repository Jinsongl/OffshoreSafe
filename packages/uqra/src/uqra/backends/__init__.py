"""Backend interfaces, discovery, and result normalization."""

from uqra.backends.base import (
    Backend,
    Capability,
    ReliabilityBackend,
    SamplingBackend,
    SensitivityBackend,
    SensitivityResult,
    normalize_capability,
)
from uqra.backends.native import NativeBackend
from uqra.backends.normalization import (
    normalize_reliability_result,
    normalize_sampling_result,
    normalize_sensitivity_result,
)
from uqra.backends.openturns import (
    OpenTURNSBackend,
    openturns_available,
    to_openturns_distribution,
    to_openturns_joint_distribution,
)
from uqra.backends.registry import BackendRegistry
from uqra.backends.uqpy import (
    UQpyBackend,
    to_uqpy_distribution,
    to_uqpy_distributions,
    uqpy_available,
)

backend_registry = BackendRegistry()
backend_registry.register(NativeBackend(), aliases=("uqra",))
backend_registry.register(OpenTURNSBackend())
backend_registry.register(UQpyBackend())


def get_backend(name: str) -> Backend:
    """Resolve a registered backend by primary name or alias."""
    return backend_registry.get(name)


def available_backends() -> tuple[str, ...]:
    """Return primary names of registered backends."""
    return backend_registry.names()


__all__ = [
    "Backend",
    "BackendRegistry",
    "Capability",
    "NativeBackend",
    "OpenTURNSBackend",
    "ReliabilityBackend",
    "SamplingBackend",
    "SensitivityBackend",
    "SensitivityResult",
    "UQpyBackend",
    "available_backends",
    "backend_registry",
    "get_backend",
    "normalize_capability",
    "normalize_reliability_result",
    "normalize_sampling_result",
    "normalize_sensitivity_result",
    "openturns_available",
    "to_openturns_distribution",
    "to_openturns_joint_distribution",
    "to_uqpy_distribution",
    "to_uqpy_distributions",
    "uqpy_available",
]
