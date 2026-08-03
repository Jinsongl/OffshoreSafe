# Tower Reliability Benchmark

This Issue #070 vertical benchmark reads a normalized OpenFAST tower-base moment
and evaluates the bending limit state
`fy * Z * 1000 - Mref * L`. Independent Normal variables represent material
strength, section modulus, and load factor. Native UQRA FORM is compared with a
closed-form first-order linearization and a fixed design-point reference.

Run from the repository root:

``` powershell
python benchmarks/offshore/tower_reliability/run.py
```
