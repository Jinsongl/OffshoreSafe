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
from uqra.backends.registry import BackendRegistry

backend_registry = BackendRegistry()
backend_registry.register(NativeBackend(), aliases=("uqra",))


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
    "ReliabilityBackend",
    "SamplingBackend",
    "SensitivityBackend",
    "SensitivityResult",
    "available_backends",
    "backend_registry",
    "get_backend",
    "normalize_capability",
    "normalize_reliability_result",
    "normalize_sampling_result",
    "normalize_sensitivity_result",
]
