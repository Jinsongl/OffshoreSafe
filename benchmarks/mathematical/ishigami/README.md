# Ishigami Sampling Benchmark

This benchmark maps three-dimensional unit-hypercube samples to
`[-pi, pi]^3` and evaluates the Ishigami function with `a = 7` and
`b = 0.1`. Its analytical mean is `a / 2 = 3.5`.

Run from the repository root with the `offshoresafe-dev` environment:

``` powershell
python benchmarks/mathematical/ishigami/run.py
```

The script reports the integration error for seeded Monte Carlo and Latin
Hypercube samples. Sobol sensitivity indices remain the responsibility of the
future sensitivity module.
