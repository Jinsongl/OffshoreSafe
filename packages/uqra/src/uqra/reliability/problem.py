"""Unified reliability problem API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from uqra.core import RandomVector
from uqra.reliability.form import FORM
from uqra.reliability.limit_state import LimitStateFunction
from uqra.reliability.monte_carlo import MonteCarloReliability
from uqra.reliability.result import ReliabilityResult
from uqra.reliability.sorm import SORM


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
        if backend.casefold() not in {"native", "uqra"}:
            raise ValueError(
                f"backend {backend!r} is not available; install a backend plugin first"
            )
        key = method.casefold().replace("-", "").replace("_", "").replace(" ", "")
        if key in {"montecarlo", "mc", "crudemc"}:
            solver = MonteCarloReliability(self.variables, self.limit_state)
        elif key in {"form", "hasoferlind", "hlrf"}:
            solver = FORM(self.variables, self.limit_state)
        elif key in {"sorm", "breitung", "hohenbichler", "tvedt"}:
            solver = SORM(self.variables, self.limit_state)
            if key != "sorm":
                options.setdefault("method", method)
            elif "correction" in options:
                options.setdefault("method", options.pop("correction"))
        else:
            raise ValueError(f"unsupported reliability method: {method}")
        self.result = solver.solve(**options)
        return self.result


__all__ = ["ReliabilityProblem"]
