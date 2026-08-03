# OffshoreSafe / UQRA

This repository develops two deliberately separated products:

- **UQRA** is the domain-independent uncertainty quantification and
  reliability framework.
- **OffshoreSafe** is the offshore engineering application layer that uses
  UQRA.

The dependency direction is `OffshoreSafe -> UQRA -> optional algorithm
backends`. UQRA does not depend on OffshoreSafe.

## Requirements and installation

UQRA requires Python 3.11 or newer. For development, activate the project
environment and install the repository in editable mode:

``` powershell
conda activate offshoresafe-dev
python -m pip install -e ".[dev]"
python -m pip install -e packages/offshoresafe
python -c "import uqra; print(uqra.__version__)"
python -c "import offshoresafe; print(offshoresafe.__version__)"
```

The latest tagged prerelease is `v0.1.0a1`. Development after that tag uses
version `0.1.0a2.dev0`.

## Public API example

``` python
from uqra import (
    FORM,
    LimitStateFunction,
    RandomVariable,
    RandomVector,
)

variables = RandomVector([
    RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
    RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
])
limit_state = LimitStateFunction(lambda x: x[0] - x[1])
result = FORM(variables, limit_state).solve()

print(result.pf, result.beta)
```

The Alpha API includes probability distributions and random vectors, Monte
Carlo/LHS/Sobol sampling, limit-state models, Monte Carlo reliability, FORM,
and SORM.

## Verification

Run the complete unit suite and quality checks from the repository root:

``` powershell
python -m pytest -q
ruff check packages tests benchmarks
ruff format --check packages tests benchmarks
```

Run the deterministic Level 0 benchmarks with:

``` powershell
python benchmarks/mathematical/core_probability/run.py
python benchmarks/mathematical/ishigami/run.py
python benchmarks/mathematical/reliability_engine/run.py
```

Benchmark definitions, reference values, and tolerances are documented under
`benchmarks/mathematical/` and in `docs/benchmark_plan.md`.

Optional backend installation, capability, and NumPy compatibility constraints
are maintained in `docs/plugin_compatibility.md`.
The versioned OffshoreSafe YAML schema is documented in
`docs/project_definition.md`.
The external solver normalization contract is documented in
`docs/solver_adapter.md`.
OpenFAST ASCII input/output integration is documented in
`docs/openfast_adapter.md`.
HEROWIND text-result integration is documented in `docs/herowind_adapter.md`.
Engineering channel statistics are documented in `docs/statistics.md`.
The configured statistics, extreme-response, and fatigue workflow is documented
in `docs/engineering_postprocessing.md`.
Tower-base bending reliability is documented in `docs/tower_reliability.md`.
