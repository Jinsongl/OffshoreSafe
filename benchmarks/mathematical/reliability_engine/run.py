"""Run the Milestone 0.4 mathematical reliability benchmarks."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parents[3] / "packages" / "uqra" / "src"))

from uqra import (
    FORM,
    SORM,
    LimitStateFunction,
    MonteCarloReliability,
    RandomVariable,
    RandomVector,
)

normal_pair = RandomVector(
    [
        RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
        RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
    ]
)
rs = LimitStateFunction(lambda x: x[..., 0] - x[..., 1])
exact_beta = 40.0 / np.sqrt(200.0)
form = FORM(normal_pair, rs).solve()
mc = MonteCarloReliability(normal_pair, rs).solve(200_000, random_state=2026)
assert abs(form.beta - exact_beta) <= 1e-5
assert abs(mc.pf - stats.norm.cdf(-exact_beta)) <= 3e-4

standard_pair = RandomVector(
    [
        RandomVariable("x1", "Normal", {"mean": 0.0, "std": 1.0}),
        RandomVariable("x2", "Normal", {"mean": 0.0, "std": 1.0}),
    ]
)


def four_branch(x: np.ndarray) -> float:
    x1, x2 = x
    return float(
        min(
            3.0 + 0.1 * (x1 - x2) ** 2 - (x1 + x2) / np.sqrt(2.0),
            3.0 + 0.1 * (x1 - x2) ** 2 + (x1 + x2) / np.sqrt(2.0),
            x1 - x2 + 7.0 / np.sqrt(2.0),
            x2 - x1 + 7.0 / np.sqrt(2.0),
        )
    )


assert (
    abs(FORM(standard_pair, LimitStateFunction(four_branch)).solve().beta - 3.0) <= 2e-4
)
nonlinear = LimitStateFunction(lambda x: 3.0 - x[0] - 0.15 * x[1] ** 2)
sorm = {
    method: SORM(standard_pair, nonlinear).solve(method).pf
    for method in ("breitung", "hohenbichler", "tvedt")
}
assert all(0.0 < pf < 1.0 for pf in sorm.values())
print({"rs_form_beta": form.beta, "rs_mc_pf": mc.pf, "sorm_pf": sorm})
