"""Native Hasofer-Lind reliability analysis."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy import stats

from uqra.core import RandomVector
from uqra.reliability.limit_state import LimitStateFunction
from uqra.reliability.result import ReliabilityResult
from uqra.reliability.transform import GaussianTransform


class FORM:
    """Find the minimum-distance failure point in standard-normal space."""

    def __init__(self, variables: RandomVector, limit_state: LimitStateFunction):
        self.variables = variables
        self.limit_state = limit_state
        self.transform = GaussianTransform(variables)

    def _g(self, u: ArrayLike) -> float:
        result = self.limit_state(self.transform.to_physical(u))
        values = np.asarray(result, dtype=float)
        if values.size != 1:
            raise ValueError("FORM requires a scalar limit-state output")
        return float(values.reshape(-1)[0])

    def gradient(self, u: ArrayLike, step: float = 1e-5) -> NDArray[np.float64]:
        point = np.asarray(u, dtype=float)
        gradient = np.empty_like(point)
        for index in range(point.size):
            delta = step * max(1.0, abs(point[index]))
            upper, lower = point.copy(), point.copy()
            upper[index] += delta
            lower[index] -= delta
            gradient[index] = (self._g(upper) - self._g(lower)) / (2.0 * delta)
        return gradient

    def solve(
        self,
        *,
        initial_point: ArrayLike | None = None,
        tolerance: float = 1e-6,
        max_iterations: int = 100,
    ) -> ReliabilityResult:
        if tolerance <= 0.0 or max_iterations <= 0:
            raise ValueError("tolerance and max_iterations must be positive")
        if initial_point is not None:
            initial = np.asarray(initial_point, dtype=float)
            if initial.shape != (self.variables.dimension,):
                raise ValueError(
                    "initial_point must have one value per random variable"
                )
            starts = [initial]
        else:
            origin = np.zeros(self.variables.dimension)
            # Small directional starts avoid a zero numerical gradient at branch
            # intersections while retaining the origin as the preferred start.
            starts = [origin]
            for index in range(self.variables.dimension):
                direction = np.zeros(self.variables.dimension)
                direction[index] = 0.1
                starts.extend((direction, -direction))

        candidates: list[tuple[np.ndarray, int, float]] = []
        for start in starts:
            point = start.copy()
            for iteration in range(1, max_iterations + 1):
                value = self._g(point)
                gradient = self.gradient(point)
                norm_squared = float(np.dot(gradient, gradient))
                if norm_squared <= np.finfo(float).eps:
                    break
                target = (
                    (float(np.dot(gradient, point)) - value) / norm_squared
                ) * gradient
                if (
                    np.linalg.norm(target - point) <= tolerance
                    and abs(value) <= tolerance
                ):
                    point = target
                    break
                # Damping improves the classical HLRF update on curved surfaces.
                step = 1.0
                current_merit = abs(value) + 0.05 * np.linalg.norm(point)
                while step > 1.0 / 128.0:
                    trial = point + step * (target - point)
                    trial_merit = abs(self._g(trial)) + 0.05 * np.linalg.norm(trial)
                    if trial_merit <= current_merit or abs(self._g(trial)) < tolerance:
                        point = trial
                        break
                    step *= 0.5
                else:
                    point = target
            residual = abs(self._g(point))
            if residual <= max(tolerance * 10.0, 1e-7):
                candidates.append((point, iteration, residual))

        if not candidates:
            raise RuntimeError("FORM design-point search did not converge")
        u_star, iteration, residual = min(
            candidates, key=lambda item: np.linalg.norm(item[0])
        )
        beta = float(np.linalg.norm(u_star))
        gradient = self.gradient(u_star)
        norm = float(np.linalg.norm(gradient))
        sensitivity = -gradient / norm if norm else np.full_like(gradient, np.nan)
        return ReliabilityResult(
            pf=float(stats.norm.cdf(-beta)),
            beta=beta,
            method="FORM (Hasofer-Lind)",
            design_point=self.transform.to_physical(u_star),
            standard_normal_design_point=u_star,
            sensitivity=sensitivity,
            converged=True,
            iterations=iteration,
            metadata={"limit_state_residual": residual},
        )


# Descriptive alias retained for users who select the algorithm by name.
HasoferLind = FORM

__all__ = ["FORM", "HasoferLind"]
