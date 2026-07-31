# Core Probability Benchmark

This benchmark covers Milestone 0.2 probability primitives. It checks
standard Normal reference values, arithmetic moments of a Lognormal
sample, and recovery of a target Gaussian correlation matrix.

Run from the repository root in the `offshoresafe-dev` environment:

``` powershell
python benchmarks/mathematical/core_probability/run.py
```

Expected values and tolerances are recorded in `expected_result.yaml`.
Analytical references follow the standard probability formulas; the
distribution parameterization is documented in `docs/api_design.md`.
