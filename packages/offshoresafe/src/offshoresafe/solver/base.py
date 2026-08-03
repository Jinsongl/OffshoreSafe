"""Solver adapter interface shared by external simulation programs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

from offshoresafe.solver.result import SolverResult


class SolverCapability(StrEnum):
    """Operations discoverable without invoking an external solver."""

    READ_INPUT = "read_input"
    READ_OUTPUT = "read_output"
    MAP_CHANNEL = "map_channel"
    EXPORT_RESULT = "export_result"


class SolverAdapter(ABC):
    """Contract for translating solver files into OffshoreSafe data.

    Concrete adapters own all solver-specific parsing and naming conventions.
    The application layer consumes only this interface and :class:`SolverResult`.
    """

    name: ClassVar[str]
    channel_map: ClassVar[Mapping[str, str]] = {}
    capabilities: ClassVar[frozenset[SolverCapability]] = frozenset(SolverCapability)

    @abstractmethod
    def read_input(self, path: str | Path) -> Mapping[str, Any]:
        """Read solver input metadata without changing the source file."""

    @abstractmethod
    def read_output(self, path: str | Path) -> SolverResult:
        """Read solver output and return a normalized time-series result."""

    def map_channel(self, source_name: str) -> str:
        """Map one solver channel to its canonical OffshoreSafe name."""

        if not isinstance(source_name, str) or not source_name.strip():
            raise ValueError("source_name must be a non-empty string")
        return self.channel_map.get(source_name, source_name)

    @abstractmethod
    def export_result(self, result: SolverResult, path: str | Path) -> Path:
        """Export a normalized result and return the resolved output path."""

    @classmethod
    def supports(cls, capability: SolverCapability | str) -> bool:
        """Return whether the adapter advertises an interface capability."""

        try:
            requested = SolverCapability(capability)
        except ValueError:
            return False
        return requested in cls.capabilities
