"""Optional Chaospy polynomial-chaos backend."""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Any

import numpy as np

from uqra.backends.base import Capability, SurrogateBackend, SurrogateResult
from uqra.core import RandomVariable, RandomVector


def _load_chaospy() -> Any:
    try:
        return import_module("chaospy")
    except (ImportError, ModuleNotFoundError) as error:
        raise RuntimeError(
            "Chaospy backend requires a working optional dependency; "
            'install UQRA with `pip install -e ".[chaospy]"`'
        ) from error


def chaospy_available() -> bool:
    """Return whether the optional Chaospy package can be discovered."""
    return find_spec("chaospy") is not None


def to_chaospy_distribution(variable: RandomVariable) -> Any:
    """Convert a supported UQRA marginal to a Chaospy distribution."""
    if not isinstance(variable, RandomVariable):
        raise TypeError("variable must be a RandomVariable")
    cp = _load_chaospy()
    parameters = variable.parameters
    key = variable.distribution.casefold().replace("-", "").replace("_", "")
    try:
        if key in {"normal", "gaussian"}:
            return cp.Normal(
                float(parameters.get("mean", 0.0)),
                float(parameters.get("std", 1.0)),
            )
        if key in {"lognormal", "lognorm"}:
            mean = float(parameters["mean"])
            std = float(parameters["std"])
            if mean <= 0.0 or std <= 0.0:
                raise ValueError("lognormal mean and std must be positive")
            sigma_squared = np.log1p((std / mean) ** 2)
            return cp.LogNormal(
                mu=float(np.log(mean) - 0.5 * sigma_squared),
                sigma=float(np.sqrt(sigma_squared)),
            )
        if key in {"weibull", "weibullmin"}:
            return cp.Weibull(
                shape=float(parameters["shape"]),
                scale=float(parameters["scale"]),
            )
        if key == "uniform":
            return cp.Uniform(float(parameters["lower"]), float(parameters["upper"]))
        raise ValueError(
            f"Chaospy backend does not support distribution {variable.distribution!r}"
        )
    except KeyError as error:
        raise ValueError(
            f"distribution {variable.distribution!r} is missing parameter "
            f"{error.args[0]!r}"
        ) from error


def to_chaospy_joint_distribution(variables: RandomVector) -> Any:
    """Convert independent UQRA marginals to a Chaospy joint distribution."""
    if not isinstance(variables, RandomVector):
        raise TypeError("variables must be a RandomVector")
    if not np.allclose(variables.correlation_matrix, np.eye(variables.dimension)):
        raise ValueError("Chaospy PCE currently requires independent variables")
    cp = _load_chaospy()
    return cp.J(
        *(to_chaospy_distribution(variable) for variable in variables.variables)
    )


def _evaluate_model(model: Any, nodes: np.ndarray) -> np.ndarray:
    evaluate = model.evaluate if hasattr(model, "evaluate") else model
    if not callable(evaluate):
        raise TypeError("model must be callable or expose evaluate(samples)")
    values = [np.asarray(evaluate(row), dtype=float) for row in nodes.T]
    result = np.asarray(values, dtype=float)
    if result.ndim == 2 and result.shape[1] == 1:
        result = result[:, 0]
    if result.ndim not in {1, 2} or not np.all(np.isfinite(result)):
        raise ValueError("model evaluations must be finite scalar or vector values")
    return result


class ChaospyBackend(SurrogateBackend):
    """Polynomial-chaos expansion adapter backed by optional Chaospy."""

    name = "chaospy"
    capabilities = frozenset(
        {
            Capability.DISTRIBUTION_NORMAL,
            Capability.DISTRIBUTION_LOGNORMAL,
            Capability.DISTRIBUTION_WEIBULL,
            Capability.DISTRIBUTION_UNIFORM,
            Capability.SURROGATE_PCE,
        }
    )

    @staticmethod
    def is_available() -> bool:
        """Return whether Chaospy is installed without importing it."""
        return chaospy_available()

    def fit_surrogate(
        self, model: Any, variables: Any, method: str = "PCE", **options: Any
    ) -> SurrogateResult:
        cp = _load_chaospy()
        key = method.casefold().replace("-", "").replace("_", "").replace(" ", "")
        if key not in {"pce", "polynomialchaos", "polynomialchaosexpansion"}:
            raise ValueError(f"unsupported Chaospy surrogate method: {method}")
        if not isinstance(variables, RandomVector):
            raise TypeError("variables must be a RandomVector")
        order = int(options.pop("order", 2))
        fit = str(options.pop("fit", "quadrature")).casefold()
        rule = str(options.pop("rule", "gaussian"))
        sparse = bool(options.pop("sparse", False))
        cross_truncation = float(options.pop("cross_truncation", 1.0))
        if order <= 0 or cross_truncation <= 0.0:
            raise ValueError("order and cross_truncation must be positive")
        distribution = to_chaospy_joint_distribution(variables)
        expansion = cp.generate_expansion(
            order,
            distribution,
            normed=True,
            cross_truncation=cross_truncation,
        )
        if fit == "quadrature":
            quadrature_order = int(options.pop("quadrature_order", order + 1))
            if quadrature_order <= 0:
                raise ValueError("quadrature_order must be positive")
            nodes, weights = cp.generate_quadrature(
                quadrature_order, distribution, rule=rule, sparse=sparse
            )
            evaluations = _evaluate_model(model, nodes)
            polynomial = cp.fit_quadrature(expansion, nodes, weights, evaluations)
        elif fit == "regression":
            n_samples = int(options.pop("n_samples", max(2 * len(expansion), 8)))
            random_state = options.pop("random_state", None)
            sample_rule = str(options.pop("sample_rule", "sobol"))
            if n_samples < len(expansion):
                raise ValueError("n_samples must be at least the PCE basis size")
            nodes = distribution.sample(n_samples, rule=sample_rule, seed=random_state)
            evaluations = _evaluate_model(model, nodes)
            polynomial = cp.fit_regression(expansion, nodes, evaluations)
            rule = sample_rule
        else:
            raise ValueError("fit must be 'quadrature' or 'regression'")
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported Chaospy options: {names}")

        def predict(samples: Any) -> np.ndarray:
            points = np.asarray(samples, dtype=float)
            single = points.ndim == 1
            points = np.atleast_2d(points)
            if points.shape[1] != variables.dimension:
                raise ValueError(
                    f"samples must have shape (n_samples, {variables.dimension})"
                )
            predictions = np.asarray(polynomial(*points.T), dtype=float)
            if predictions.ndim > 1:
                predictions = np.moveaxis(predictions, -1, 0)
            return predictions[0] if single else predictions

        return SurrogateResult(
            method="PCE (Chaospy)",
            surrogate=predict,
            statistics={
                "mean": np.asarray(cp.E(polynomial, distribution), dtype=float),
                "variance": np.asarray(cp.Var(polynomial, distribution), dtype=float),
                "standard_deviation": np.asarray(
                    cp.Std(polynomial, distribution), dtype=float
                ),
            },
            metadata={
                "backend": self.name,
                "backend_version": cp.__version__,
                "algorithm": "PCE",
                "fit": fit,
                "order": order,
                "basis_size": len(expansion),
                "training_samples": int(nodes.shape[1]),
                "rule": rule,
                "sparse": sparse,
            },
        )


__all__ = [
    "ChaospyBackend",
    "chaospy_available",
    "to_chaospy_distribution",
    "to_chaospy_joint_distribution",
]
