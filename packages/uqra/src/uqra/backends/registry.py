"""Backend registration and lookup."""

from __future__ import annotations

from collections.abc import Iterable

from uqra.backends.base import Backend


def _name(value: str) -> str:
    name = value.strip().casefold()
    if not name:
        raise ValueError("backend name must be a non-empty string")
    return name


class BackendRegistry:
    """Explicit registry for built-in and optional backend adapters."""

    def __init__(self) -> None:
        self._backends: dict[str, Backend] = {}

    def register(
        self,
        backend: Backend,
        *,
        aliases: Iterable[str] = (),
        replace: bool = False,
    ) -> None:
        if not isinstance(backend, Backend):
            raise TypeError("backend must implement the Backend interface")
        names = {_name(backend.name), *(_name(alias) for alias in aliases)}
        conflicts = names.intersection(self._backends)
        if conflicts and not replace:
            raise ValueError(f"backend name already registered: {sorted(conflicts)[0]}")
        for name in names:
            self._backends[name] = backend

    def get(self, name: str) -> Backend:
        try:
            return self._backends[_name(name)]
        except KeyError as error:
            raise ValueError(
                f"backend {name!r} is not available; install and register a backend plugin"
            ) from error

    def names(self) -> tuple[str, ...]:
        """Return registered primary backend names without aliases."""
        return tuple(
            sorted({_name(backend.name) for backend in self._backends.values()})
        )


__all__ = ["BackendRegistry"]
