"""Optional OpenTURNS reliability backend.

This module deliberately imports OpenTURNS only when an adapter operation is
requested, so importing :mod:`uqra` never requires the optional dependency.
"""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Any

import numpy as np

from uqra.backends.base import Capability, ReliabilityBackend
from uqra.core import RandomVariable, RandomVector
from uqra.reliability import ReliabilityResult


def _method_key(method: str) -> str:
    return method.casefold().replace("-", "").replace("_", "").replace(" ", "")


def _load_openturns() -> Any:
    try:
        return import_module("openturns")
    except ModuleNotFoundError as error:
        if error.name != "openturns":
            raise
        raise RuntimeError(
            "OpenTURNS backend requires the optional dependency; "
            'install UQRA with `pip install -e ".[openturns]"`'
        ) from error


def openturns_available() -> bool:
    """Return whether the optional OpenTURNS package can be discovered."""
    return find_spec("openturns") is not None


def to_openturns_distribution(variable: RandomVariable) -> Any:
    """Convert a supported UQRA random variable to an OpenTURNS marginal."""
    if not isinstance(variable, RandomVariable):
        raise TypeError("variable must be a RandomVariable")
    ot = _load_openturns()
    parameters = variable.parameters
    key = variable.distribution.casefold().replace("-", "").replace("_", "")
    try:
        if key in {"normal", "gaussian"}:
            result = ot.Normal(
                float(parameters.get("mean", 0.0)),
                float(parameters.get("std", 1.0)),
            )
        elif key in {"lognormal", "lognorm"}:
            result = ot.LogNormalMuSigma(
                float(parameters["mean"]),
                float(parameters["std"]),
                0.0,
            ).getDistribution()
        elif key in {"weibull", "weibullmin"}:
            result = ot.WeibullMin(
                float(parameters["scale"]),
                float(parameters["shape"]),
            )
        elif key == "uniform":
            result = ot.Uniform(
                float(parameters["lower"]),
                float(parameters["upper"]),
            )
        else:
            raise ValueError(
                f"OpenTURNS backend does not support distribution "
                f"{variable.distribution!r}"
            )
    except KeyError as error:
        raise ValueError(
            f"distribution {variable.distribution!r} is missing parameter "
            f"{error.args[0]!r}"
        ) from error
    result.setDescription([variable.name])
    return result


def to_openturns_joint_distribution(variables: RandomVector) -> Any:
    """Convert UQRA marginals and Gaussian dependence to OpenTURNS."""
    if not isinstance(variables, RandomVector):
        raise TypeError("variables must be a RandomVector")
    ot = _load_openturns()
    marginals = [to_openturns_distribution(item) for item in variables.variables]
    if np.allclose(variables.correlation_matrix, np.eye(variables.dimension)):
        result = ot.JointDistribution(marginals)
        result.setDescription(list(variables.names))
        return result
    correlation = ot.CorrelationMatrix(variables.dimension)
    for row in range(variables.dimension):
        for column in range(row):
            correlation[row, column] = float(variables.correlation_matrix[row, column])
    copula = ot.NormalCopula(correlation)
    result = ot.JointDistribution(marginals, copula)
    result.setDescription(list(variables.names))
    return result


class OpenTURNSBackend(ReliabilityBackend):
    """FORM and SORM adapter backed by an optional OpenTURNS installation."""

    name = "openturns"
    capabilities = frozenset(
        {
            Capability.DISTRIBUTION_NORMAL,
            Capability.DISTRIBUTION_LOGNORMAL,
            Capability.DISTRIBUTION_WEIBULL,
            Capability.DISTRIBUTION_UNIFORM,
            Capability.RELIABILITY_FORM,
            Capability.RELIABILITY_SORM,
        }
    )

    @staticmethod
    def is_available() -> bool:
        """Return whether OpenTURNS is installed without importing it."""
        return openturns_available()

    def solve_reliability(
        self, problem: Any, method: str, **options: Any
    ) -> ReliabilityResult:
        ot = _load_openturns()
        key = _method_key(method)
        if key in {"form", "hasoferlind", "hlrf"}:
            algorithm_name = "FORM"
            correction = None
        elif key in {"sorm", "breitung", "hohenbichler", "tvedt"}:
            algorithm_name = "SORM"
            correction = options.pop("correction", None)
            if key != "sorm":
                correction = method
            correction = str(correction or "Breitung").casefold()
            if correction not in {"breitung", "hohenbichler", "tvedt"}:
                raise ValueError(
                    "SORM correction must be Breitung, Hohenbichler, or Tvedt"
                )
        else:
            raise ValueError(f"unsupported OpenTURNS reliability method: {method}")

        distribution = to_openturns_joint_distribution(problem.variables)

        def evaluate(point: Any) -> list[float]:
            value = problem.limit_state.evaluate(np.asarray(point, dtype=float))
            values = np.asarray(value, dtype=float)
            if values.size != 1:
                raise ValueError("OpenTURNS reliability requires a scalar limit state")
            return [float(values.reshape(-1)[0])]

        function = ot.PythonFunction(problem.variables.dimension, 1, evaluate)
        input_vector = ot.RandomVector(distribution)
        output_vector = ot.CompositeRandomVector(function, input_vector)
        event = ot.ThresholdEvent(output_vector, ot.LessOrEqual(), 0.0)
        optimizer = ot.Cobyla()
        tolerance = float(options.pop("tolerance", 1.0e-6))
        max_iterations = int(options.pop("max_iterations", 1000))
        if tolerance <= 0.0 or max_iterations <= 0:
            raise ValueError("tolerance and max_iterations must be positive")
        if options:
            names = ", ".join(sorted(options))
            raise TypeError(f"unsupported OpenTURNS options: {names}")
        optimizer.setMaximumIterationNumber(max_iterations)
        optimizer.setMaximumAbsoluteError(tolerance)
        optimizer.setMaximumRelativeError(tolerance)
        optimizer.setMaximumResidualError(tolerance)
        optimizer.setMaximumConstraintError(tolerance)
        algorithm = ot.FORM() if algorithm_name == "FORM" else ot.SORM()
        algorithm.setNearestPointAlgorithm(optimizer)
        algorithm.setEvent(event)
        algorithm.setPhysicalStartingPoint(distribution.getMean())
        algorithm.run()
        result = algorithm.getResult()
        return self._normalize_result(ot, result, algorithm_name, correction)

    def _normalize_result(
        self, ot: Any, result: Any, algorithm: str, correction: str | None
    ) -> ReliabilityResult:
        if algorithm == "FORM":
            pf = float(result.getEventProbability())
            beta = float(result.getHasoferReliabilityIndex())
            method = "FORM (OpenTURNS)"
        else:
            suffix = str(correction).capitalize()
            pf = float(getattr(result, f"getEventProbability{suffix}")())
            beta = float(getattr(result, f"getGeneralisedReliabilityIndex{suffix}")())
            method = f"SORM (OpenTURNS {suffix})"
        optimization = result.getOptimizationResult()
        return ReliabilityResult(
            pf=pf,
            beta=beta,
            method=method,
            design_point=np.asarray(result.getPhysicalSpaceDesignPoint(), dtype=float),
            standard_normal_design_point=np.asarray(
                result.getStandardSpaceDesignPoint(), dtype=float
            ),
            sensitivity=np.asarray(result.getImportanceFactors(), dtype=float),
            converged=True,
            iterations=int(optimization.getIterationNumber()),
            metadata={
                "backend": self.name,
                "backend_version": ot.__version__,
                "algorithm": algorithm,
                "correction": correction,
                "optimizer": optimizer_name(optimization),
            },
        )


def optimizer_name(result: Any) -> str:
    """Return stable optimizer metadata across OpenTURNS versions."""
    return (
        str(result.getAlgorithmName())
        if hasattr(result, "getAlgorithmName")
        else "Cobyla"
    )


__all__ = [
    "OpenTURNSBackend",
    "openturns_available",
    "to_openturns_distribution",
    "to_openturns_joint_distribution",
]
