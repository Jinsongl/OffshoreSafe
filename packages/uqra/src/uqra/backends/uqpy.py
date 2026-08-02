"""Optional UQpy sampling and reliability backend."""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Any

import numpy as np

from uqra.backends.base import Capability, ReliabilityBackend, SamplingBackend
from uqra.core import RandomVariable, RandomVector
from uqra.reliability import ReliabilityResult
from uqra.sampling import SamplingResult


def _method_key(method: str) -> str:
    return method.casefold().replace("-", "").replace("_", "").replace(" ", "")


def _load_uqpy() -> Any:
    try:
        return import_module("UQpy")
    except (ImportError, ModuleNotFoundError) as error:
        raise RuntimeError(
            "UQpy backend requires a working optional dependency; "
            'install UQRA with `pip install -e ".[uqpy]"`'
        ) from error


def uqpy_available() -> bool:
    """Return whether UQpy and its legacy pkg_resources dependency exist."""
    return find_spec("UQpy") is not None and find_spec("pkg_resources") is not None


def to_uqpy_distribution(variable: RandomVariable) -> Any:
    """Convert a supported UQRA marginal to a UQpy distribution."""
    if not isinstance(variable, RandomVariable):
        raise TypeError("variable must be a RandomVariable")
    _load_uqpy()
    distributions = import_module("UQpy.distributions")
    parameters = variable.parameters
    key = variable.distribution.casefold().replace("-", "").replace("_", "")
    try:
        if key in {"normal", "gaussian"}:
            return distributions.Normal(
                loc=float(parameters.get("mean", 0.0)),
                scale=float(parameters.get("std", 1.0)),
            )
        if key in {"lognormal", "lognorm"}:
            mean = float(parameters["mean"])
            std = float(parameters["std"])
            if mean <= 0.0 or std <= 0.0:
                raise ValueError("lognormal mean and std must be positive")
            sigma_squared = np.log1p((std / mean) ** 2)
            return distributions.Lognormal(
                s=float(np.sqrt(sigma_squared)),
                scale=float(np.exp(np.log(mean) - 0.5 * sigma_squared)),
            )
        if key == "uniform":
            lower = float(parameters["lower"])
            upper = float(parameters["upper"])
            if upper <= lower:
                raise ValueError("uniform upper must be greater than lower")
            return distributions.Uniform(loc=lower, scale=upper - lower)
        raise ValueError(
            f"UQpy backend does not support distribution {variable.distribution!r}"
        )
    except KeyError as error:
        raise ValueError(
            f"distribution {variable.distribution!r} is missing parameter "
            f"{error.args[0]!r}"
        ) from error


def to_uqpy_distributions(variables: RandomVector) -> list[Any]:
    """Convert a UQRA random vector to UQpy marginals."""
    if not isinstance(variables, RandomVector):
        raise TypeError("variables must be a RandomVector")
    return [to_uqpy_distribution(variable) for variable in variables.variables]


class _LimitStateModel:
    """Minimal UQpy RunModel protocol around a UQRA limit state."""

    def __init__(self, limit_state: Any) -> None:
        self.limit_state = limit_state

    def initialize(self, samples: Any) -> None:
        pass

    def finalize(self) -> None:
        pass

    def preprocess_single_sample(self, index: int, sample: Any) -> np.ndarray:
        return np.asarray(sample, dtype=float)

    def execute_single_sample(self, index: int, sample: Any) -> float:
        values = np.asarray(self.limit_state.evaluate(sample), dtype=float)
        if values.size != 1:
            raise ValueError("UQpy reliability requires a scalar limit state")
        return float(values.reshape(-1)[0])

    def postprocess_single_file(self, index: int, output: Any) -> float:
        return float(output)


class UQpyBackend(ReliabilityBackend, SamplingBackend):
    """Adapter for UQpy Monte Carlo/LHS sampling and FORM/SORM."""

    name = "uqpy"
    capabilities = frozenset(
        {
            Capability.DISTRIBUTION_NORMAL,
            Capability.DISTRIBUTION_LOGNORMAL,
            Capability.DISTRIBUTION_UNIFORM,
            Capability.SAMPLING_MONTE_CARLO,
            Capability.SAMPLING_LATIN_HYPERCUBE,
            Capability.RELIABILITY_FORM,
            Capability.RELIABILITY_SORM,
        }
    )

    @staticmethod
    def is_available() -> bool:
        """Return whether the optional runtime can be discovered."""
        return uqpy_available()

    def sample(
        self,
        method: str,
        dimension: int,
        n_samples: int,
        *,
        random_state: Any = None,
        **options: Any,
    ) -> SamplingResult:
        uqpy = _load_uqpy()
        if not isinstance(dimension, int) or isinstance(dimension, bool):
            raise TypeError("dimension must be an integer")
        if not isinstance(n_samples, int) or isinstance(n_samples, bool):
            raise TypeError("n_samples must be an integer")
        if dimension <= 0 or n_samples <= 0:
            raise ValueError("dimension and n_samples must be positive")
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported UQpy sampling options: {names}")
        distributions = import_module("UQpy.distributions")
        sampling = import_module("UQpy.sampling")
        marginals = [distributions.Uniform(loc=0.0, scale=1.0)] * dimension
        key = _method_key(method)
        if key in {"montecarlo", "mc"}:
            algorithm = sampling.MonteCarloSampling(
                marginals, nsamples=n_samples, random_state=random_state
            )
            samples = algorithm.samples
            algorithm_name = "MonteCarloSampling"
        elif key in {"latinhypercube", "lhs"}:
            algorithm = sampling.LatinHypercubeSampling(
                marginals, nsamples=n_samples, random_state=random_state
            )
            samples = algorithm.samplesU01
            algorithm_name = "LatinHypercubeSampling"
        else:
            raise ValueError(f"unsupported UQpy sampling method: {method}")
        return SamplingResult(
            samples=np.asarray(samples, dtype=float),
            metadata={
                "backend": self.name,
                "backend_version": uqpy.__version__,
                "algorithm": algorithm_name,
                "method": method,
                "dimension": dimension,
                "n_samples": n_samples,
                "random_state": random_state,
            },
        )

    def solve_reliability(
        self, problem: Any, method: str, **options: Any
    ) -> ReliabilityResult:
        uqpy = _load_uqpy()
        reliability = import_module("UQpy.reliability.taylor_series")
        run_model_module = import_module("UQpy.run_model")
        key = _method_key(method)
        if key not in {"form", "hasoferlind", "hlrf", "sorm", "breitung"}:
            raise ValueError(f"unsupported UQpy reliability method: {method}")
        df_step = float(options.pop("df_step", 0.01))
        max_iterations = int(options.pop("max_iterations", 100))
        tolerance = float(options.pop("tolerance", 1.0e-3))
        seed_u = np.asarray(
            options.pop("seed_u", np.zeros(problem.variables.dimension)), dtype=float
        )
        if df_step <= 0.0 or max_iterations <= 0 or tolerance <= 0.0:
            raise ValueError("df_step, max_iterations, and tolerance must be positive")
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported UQpy reliability options: {names}")
        run_model = run_model_module.RunModel(_LimitStateModel(problem.limit_state))
        form = reliability.FORM(
            distributions=to_uqpy_distributions(problem.variables),
            runmodel_object=run_model,
            seed_u=seed_u,
            df_step=df_step,
            corr_x=np.asarray(problem.variables.correlation_matrix, dtype=float),
            n_iterations=max_iterations,
            tolerance_u=tolerance,
            tolerance_beta=tolerance,
            tolerance_gradient=tolerance,
        )
        if key in {"sorm", "breitung"}:
            # UQpy 4.2 truncates the final FORM gradient record. Re-evaluate it
            # at the converged design point before its SORM curvature step.
            gradient, _, _ = form._derivatives(
                point_u=form.design_point_u[-1],
                point_x=np.atleast_2d(form.design_point_x[-1]),
                runmodel_object=run_model,
                nataf_object=form.nataf_object,
                df_step=df_step,
                order="first",
            )
            form.state_function_gradient_record = [np.asarray(gradient, dtype=float)]
            sorm = reliability.SORM(form)
            pf = float(np.asarray(sorm.failure_probability).reshape(-1)[-1])
            beta = float(np.asarray(sorm.beta_second_order).reshape(-1)[-1])
            algorithm_name = "SORM"
        else:
            pf = float(form.failure_probability[-1])
            beta = float(form.beta[-1])
            algorithm_name = "FORM"
        iterations = int(form.iterations[-1])
        return ReliabilityResult(
            pf=pf,
            beta=beta,
            method=f"{algorithm_name} (UQpy)",
            design_point=np.asarray(form.design_point_x[-1], dtype=float),
            standard_normal_design_point=np.asarray(
                form.design_point_u[-1], dtype=float
            ),
            sensitivity=np.asarray(form.alpha, dtype=float),
            converged=iterations < max_iterations,
            iterations=iterations,
            metadata={
                "backend": self.name,
                "backend_version": uqpy.__version__,
                "algorithm": algorithm_name,
                "optimizer": "HLRF",
                "df_step": df_step,
            },
        )


__all__ = [
    "UQpyBackend",
    "to_uqpy_distribution",
    "to_uqpy_distributions",
    "uqpy_available",
]
