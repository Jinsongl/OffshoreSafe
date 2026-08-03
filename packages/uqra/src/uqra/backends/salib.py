"""Optional SALib global-sensitivity backend."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import version
from importlib.util import find_spec
from typing import Any

import numpy as np

from uqra.backends.base import Capability, SensitivityBackend, SensitivityResult
from uqra.core import RandomVector


def _load_salib() -> Any:
    try:
        return import_module("SALib")
    except (ImportError, ModuleNotFoundError) as error:
        raise RuntimeError(
            "SALib backend requires a working optional dependency; "
            'install UQRA with `pip install -e ".[salib]"`'
        ) from error


def salib_available() -> bool:
    """Return whether the optional SALib package can be discovered."""
    return find_spec("SALib") is not None


def to_salib_problem(variables: RandomVector) -> dict[str, Any]:
    """Convert independent uniform UQRA variables to a SALib problem."""
    if not isinstance(variables, RandomVector):
        raise TypeError("variables must be a RandomVector")
    if not np.allclose(variables.correlation_matrix, np.eye(variables.dimension)):
        raise ValueError("SALib sensitivity currently requires independent variables")
    bounds: list[list[float]] = []
    for variable in variables.variables:
        key = variable.distribution.casefold().replace("-", "").replace("_", "")
        if key != "uniform":
            raise ValueError("SALib sensitivity currently requires Uniform variables")
        try:
            lower = float(variable.parameters["lower"])
            upper = float(variable.parameters["upper"])
        except KeyError as error:
            raise ValueError(
                f"distribution {variable.distribution!r} is missing parameter "
                f"{error.args[0]!r}"
            ) from error
        if upper <= lower:
            raise ValueError("uniform upper must be greater than lower")
        bounds.append([lower, upper])
    return {
        "num_vars": variables.dimension,
        "names": list(variables.names),
        "bounds": bounds,
    }


def _evaluate_model(model: Any, samples: np.ndarray) -> np.ndarray:
    evaluate = model.evaluate if hasattr(model, "evaluate") else model
    if not callable(evaluate):
        raise TypeError("model must be callable or expose evaluate(samples)")
    values = np.asarray(
        [np.asarray(evaluate(row), dtype=float) for row in samples], dtype=float
    )
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]
    if values.ndim != 1 or not np.all(np.isfinite(values)):
        raise ValueError("sensitivity model must return one finite scalar per sample")
    return values


def _arrays(result: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    return {
        name: np.asarray(result[name], dtype=float) for name in names if name in result
    }


class SALibBackend(SensitivityBackend):
    """Sobol indices and Morris screening backed by optional SALib."""

    name = "salib"
    capabilities = frozenset(
        {Capability.SENSITIVITY_SOBOL, Capability.SENSITIVITY_MORRIS}
    )

    @staticmethod
    def is_available() -> bool:
        """Return whether SALib is installed without importing it."""
        return salib_available()

    def analyze_sensitivity(
        self, model: Any, method: str, **options: Any
    ) -> SensitivityResult:
        _load_salib()
        variables = options.pop("variables", None)
        problem = options.pop("problem", None)
        if variables is not None and problem is not None:
            raise ValueError("provide only one of variables and problem")
        if variables is not None:
            problem = to_salib_problem(variables)
        if not isinstance(problem, dict):
            raise TypeError(
                "variables must be a RandomVector or problem must be a mapping"
            )
        names = list(problem.get("names", ()))
        bounds = list(problem.get("bounds", ()))
        if int(problem.get("num_vars", 0)) != len(names) or len(bounds) != len(names):
            raise ValueError("SALib problem num_vars, names, and bounds must agree")
        n_samples = int(options.pop("n_samples", 1024))
        random_state = options.pop("random_state", None)
        num_resamples = int(options.pop("num_resamples", 100))
        conf_level = float(options.pop("conf_level", 0.95))
        if n_samples <= 0 or num_resamples <= 0:
            raise ValueError("n_samples and num_resamples must be positive")
        if not 0.0 < conf_level < 1.0:
            raise ValueError("conf_level must be between zero and one")
        key = method.casefold().replace("-", "").replace("_", "").replace(" ", "")
        if key in {"sobol", "sobolindices"}:
            return self._sobol(
                model,
                problem,
                n_samples,
                random_state,
                num_resamples,
                conf_level,
                options,
            )
        if key in {"morris", "morrisscreening", "elementaryeffects"}:
            return self._morris(
                model,
                problem,
                n_samples,
                random_state,
                num_resamples,
                conf_level,
                options,
            )
        raise ValueError(f"unsupported SALib sensitivity method: {method}")

    def _sobol(
        self,
        model: Any,
        problem: dict[str, Any],
        n_samples: int,
        random_state: Any,
        num_resamples: int,
        conf_level: float,
        options: dict[str, Any],
    ) -> SensitivityResult:
        sample = import_module("SALib.sample.sobol")
        analyze = import_module("SALib.analyze.sobol")
        calc_second_order = bool(options.pop("calc_second_order", True))
        scramble = bool(options.pop("scramble", True))
        skip_values = int(options.pop("skip_values", 0))
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported SALib Sobol options: {names}")
        samples = sample.sample(
            problem,
            n_samples,
            calc_second_order=calc_second_order,
            scramble=scramble,
            skip_values=skip_values,
            seed=random_state,
        )
        values = _evaluate_model(model, samples)
        result = analyze.analyze(
            problem,
            values,
            calc_second_order=calc_second_order,
            num_resamples=num_resamples,
            conf_level=conf_level,
            print_to_console=False,
            seed=random_state,
        )
        indices = _arrays(result, ("S1", "S1_conf", "ST", "ST_conf", "S2", "S2_conf"))
        indices["names"] = tuple(problem["names"])
        return self._result("Sobol (SALib)", "Sobol", indices, n_samples, samples)

    def _morris(
        self,
        model: Any,
        problem: dict[str, Any],
        n_samples: int,
        random_state: Any,
        num_resamples: int,
        conf_level: float,
        options: dict[str, Any],
    ) -> SensitivityResult:
        sample = import_module("SALib.sample.morris")
        analyze = import_module("SALib.analyze.morris")
        num_levels = int(options.pop("num_levels", 4))
        optimal_trajectories = options.pop("optimal_trajectories", None)
        local_optimization = bool(options.pop("local_optimization", True))
        scaled = bool(options.pop("scaled", False))
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported SALib Morris options: {names}")
        samples = sample.sample(
            problem,
            n_samples,
            num_levels=num_levels,
            optimal_trajectories=optimal_trajectories,
            local_optimization=local_optimization,
            seed=random_state,
        )
        values = _evaluate_model(model, samples)
        result = analyze.analyze(
            problem,
            samples,
            values,
            num_resamples=num_resamples,
            conf_level=conf_level,
            scaled=scaled,
            print_to_console=False,
            num_levels=num_levels,
            seed=random_state,
        )
        indices = _arrays(result, ("mu", "mu_star", "sigma", "mu_star_conf"))
        indices["names"] = tuple(problem["names"])
        ranking = np.argsort(-indices["mu_star"])
        indices["ranking"] = tuple(problem["names"][index] for index in ranking)
        return self._result("Morris (SALib)", "Morris", indices, n_samples, samples)

    def _result(
        self,
        method: str,
        algorithm: str,
        indices: dict[str, Any],
        n_samples: int,
        samples: np.ndarray,
    ) -> SensitivityResult:
        return SensitivityResult(
            method=method,
            indices=indices,
            metadata={
                "backend": self.name,
                "backend_version": version("SALib"),
                "algorithm": algorithm,
                "base_samples": n_samples,
                "model_evaluations": int(samples.shape[0]),
            },
        )


__all__ = ["SALibBackend", "salib_available", "to_salib_problem"]
