"""Second-order reliability probability approximations."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
from scipy import stats

from uqra.core import RandomVector
from uqra.reliability.form import FORM
from uqra.reliability.limit_state import LimitStateFunction
from uqra.reliability.result import ReliabilityResult


class SORM:
    """Apply Breitung, Hohenbichler, or Tvedt curvature corrections."""

    _METHODS: ClassVar[set[str]] = {"breitung", "hohenbichler", "tvedt"}

    def __init__(self, variables: RandomVector, limit_state: LimitStateFunction):
        self.form = FORM(variables, limit_state)

    def _curvatures(self, point: np.ndarray, step: float = 2e-4) -> np.ndarray:
        dimension = point.size
        gradient = self.form.gradient(point)
        norm = np.linalg.norm(gradient)
        if dimension == 1:
            return np.empty(0)
        hessian = np.empty((dimension, dimension))
        for index in range(dimension):
            delta = step * max(1.0, abs(point[index]))
            upper, lower = point.copy(), point.copy()
            upper[index] += delta
            lower[index] -= delta
            hessian[:, index] = (
                self.form.gradient(upper) - self.form.gradient(lower)
            ) / (2.0 * delta)
        hessian = (hessian + hessian.T) / 2.0
        normal = gradient / norm
        basis = np.linalg.qr(np.column_stack((normal, np.eye(dimension))))[0][:, 1:]
        return np.linalg.eigvalsh(basis.T @ hessian @ basis / norm)

    @staticmethod
    def _factor(value: complex, curvatures: np.ndarray) -> complex:
        return np.prod((1.0 + value * curvatures).astype(complex) ** -0.5)

    def solve(
        self, method: str = "breitung", **form_options: object
    ) -> ReliabilityResult:
        selected = method.lower()
        if selected not in self._METHODS:
            raise ValueError("method must be Breitung, Hohenbichler, or Tvedt")
        first_order = self.form.solve(**form_options)
        point = np.asarray(first_order.standard_normal_design_point)
        curvatures = self._curvatures(point)
        beta = first_order.beta
        phi = float(stats.norm.pdf(beta))
        base_pf = float(stats.norm.cdf(-beta))
        if selected == "breitung":
            pf = base_pf * self._factor(beta, curvatures).real
        elif selected == "hohenbichler":
            pf = base_pf * self._factor(phi / base_pf, curvatures).real
        else:
            a = self._factor(beta, curvatures)
            b = self._factor(beta + 1.0, curvatures)
            c = self._factor(complex(beta, 1.0), curvatures).real
            coefficient = beta * base_pf - phi
            pf = (
                base_pf * a
                + coefficient * (a - b)
                + (beta + 1.0) * coefficient * (a - c)
            ).real
        pf = float(np.clip(pf, 0.0, 1.0))
        return ReliabilityResult(
            pf=pf,
            beta=float(-stats.norm.ppf(pf)),
            method=f"SORM ({selected.title()})",
            design_point=first_order.design_point,
            standard_normal_design_point=point,
            sensitivity=first_order.sensitivity,
            converged=True,
            iterations=first_order.iterations,
            metadata={"form_beta": beta, "principal_curvatures": curvatures},
        )
