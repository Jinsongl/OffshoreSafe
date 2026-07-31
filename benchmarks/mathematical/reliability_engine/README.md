# Reliability Engine Benchmark

This Level 0 benchmark validates Milestone 0.4 without an optional backend.

- R-S: independent `R ~ Normal(100, 10)` and `S ~ Normal(60, 10)`, with
  `g = R - S`. FORM is checked against the analytical reliability index
  `40 / sqrt(200)` and Monte Carlo against the analytical failure probability.
- Four Branch: FORM starts at the origin and must locate the nearest design
  point with reliability index 3.
- Nonlinear surface: all three SORM corrections must return finite
  probabilities and principal curvatures.

Run `python benchmarks/mathematical/reliability_engine/run.py` from the
repository root in the `offshoresafe-dev` environment.

Analytical targets and tolerances are recorded in `expected_result.yaml`.
