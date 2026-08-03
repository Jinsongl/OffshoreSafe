# Blade Fatigue Reliability Benchmark

This Issue #071 vertical benchmark reads an OpenFAST blade-root moment, applies
rainflow counting, scales the cycle block to an assessed lifetime, and evaluates
`g = D_limit - D`. Independent load-factor and S-N parameter uncertainties are
solved with native UQRA FORM. The result is checked against analytical Miner
damage and a fixed design-point reference.

Run from the repository root:

``` powershell
python benchmarks/offshore/blade_fatigue_reliability/run.py
```
