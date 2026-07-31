"""Verify that the backend facade preserves native algorithm behavior."""

from __future__ import annotations

import numpy as np
from uqra import (
    FORM,
    LimitStateFunction,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
    get_backend,
)

variables = RandomVector(
    [
        RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
        RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
    ]
)
limit_state = LimitStateFunction(lambda x: x[0] - x[1])
direct = FORM(variables, limit_state).solve()
dispatched = ReliabilityProblem(variables, limit_state).solve("FORM", backend="native")
assert np.isclose(dispatched.beta, direct.beta)
assert np.isclose(dispatched.pf, direct.pf)

samples = get_backend("native").sample("Sobol", 2, 16, random_state=42)  # type: ignore[attr-defined]
assert samples.samples.shape == (16, 2)
assert samples.metadata["balance_guaranteed"] is True
print({"form_beta": dispatched.beta, "sampling_method": samples.metadata["method"]})
