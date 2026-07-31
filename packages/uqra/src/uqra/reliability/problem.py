"""Unified reliability problem API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from uqra.core import RandomVector
from uqra.reliability.limit_state import LimitStateFunction
from uqra.reliability.result import ReliabilityResult


class ReliabilityProblem:
    """Combine uncertainty and failure definition behind one solve method."""

    def __init__(
        self,
        variables: RandomVector,
        limit_state: LimitStateFunction | Callable[..., Any] | object,
    ) -> None:
        if not isinstance(variables, RandomVector):
            raise TypeError("variables must be a RandomVector")
        self.variables = variables
        if isinstance(limit_state, LimitStateFunction):
            self.limit_state = limit_state
        elif callable(limit_state) or callable(getattr(limit_state, "evaluate", None)):
            self.limit_state = LimitStateFunction(limit_state)
        else:
            raise TypeError("limit_state must be callable or provide evaluate(inputs)")
        self.result: ReliabilityResult | None = None

    def solve(
        self,
        method: str = "FORM",
        backend: str = "native",
        **options: Any,
    ) -> ReliabilityResult:
        from uqra.backends import ReliabilityBackend, get_backend

        selected = get_backend(backend)
        if not isinstance(selected, ReliabilityBackend):
            raise ValueError(
                f"backend {backend!r} does not provide reliability methods"
            )
        self.result = selected.solve_reliability(self, method, **options)
        return self.result


__all__ = ["ReliabilityProblem"]
