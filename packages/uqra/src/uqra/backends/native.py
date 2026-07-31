"""Adapter exposing built-in UQRA algorithms through backend contracts."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from uqra.backends.base import Capability, ReliabilityBackend, SamplingBackend
from uqra.backends.normalization import (
    normalize_reliability_result,
    normalize_sampling_result,
)
from uqra.reliability.form import FORM
from uqra.reliability.monte_carlo import MonteCarloReliability
from uqra.reliability.sorm import SORM
from uqra.sampling import LatinHypercubeSampler, MonteCarloSampler, SobolSampler


def _method_key(method: str) -> str:
    return method.casefold().replace("-", "").replace("_", "").replace(" ", "")


class NativeBackend(ReliabilityBackend, SamplingBackend):
    """Backend facade for algorithms shipped directly with UQRA."""

    name = "native"
    capabilities = frozenset(
        {
            Capability.RELIABILITY_MONTE_CARLO,
            Capability.RELIABILITY_FORM,
            Capability.RELIABILITY_SORM,
            Capability.SAMPLING_MONTE_CARLO,
            Capability.SAMPLING_LATIN_HYPERCUBE,
            Capability.SAMPLING_SOBOL,
        }
    )

    def solve_reliability(self, problem: Any, method: str, **options: Any) -> Any:
        key = _method_key(method)
        if key in {"montecarlo", "mc", "crudemc"}:
            solver = MonteCarloReliability(problem.variables, problem.limit_state)
        elif key in {"form", "hasoferlind", "hlrf"}:
            solver = FORM(problem.variables, problem.limit_state)
        elif key in {"sorm", "breitung", "hohenbichler", "tvedt"}:
            solver = SORM(problem.variables, problem.limit_state)
            if key != "sorm":
                options.setdefault("method", method)
            elif "correction" in options:
                options.setdefault("method", options.pop("correction"))
        else:
            raise ValueError(f"unsupported reliability method: {method}")
        result = normalize_reliability_result(solver.solve(**options))
        return replace(result, metadata={**result.metadata, "backend": self.name})

    def sample(
        self,
        method: str,
        dimension: int,
        n_samples: int,
        *,
        random_state: Any = None,
        **options: Any,
    ) -> Any:
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported native sampling options: {names}")
        key = _method_key(method)
        if key in {"montecarlo", "mc"}:
            sampler = MonteCarloSampler(dimension)
        elif key in {"latinhypercube", "lhs"}:
            sampler = LatinHypercubeSampler(dimension)
        elif key == "sobol":
            sampler = SobolSampler(dimension)
        else:
            raise ValueError(f"unsupported sampling method: {method}")
        result = normalize_sampling_result(
            sampler.sample(n_samples, random_state=random_state)
        )
        return type(result)(
            samples=result.samples,
            metadata={**result.metadata, "backend": self.name},
        )


__all__ = ["NativeBackend"]
