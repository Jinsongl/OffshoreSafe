# Hs-Tp IFORM Environmental Contour Benchmark

This Issues #080/#081 benchmark defines correlated Weibull significant wave
height and Lognormal peak period marginals. Fixed `input.yaml` and
`expected_result.yaml` files define the release reference. The automated
acceptance verifies the 50-year daily-event IFORM reliability radius, constant
standard-normal norm, positive physical points, named units, and a fixed
SciPy-based physical reference point.

The run also emits the template v1.1 Markdown, Excel, and PDF engineering
reports plus a standalone traceability manifest under `output/`. Acceptance
requires the numerical checks, report status, manifest completeness, and all
source-file hash audits to pass.

Run from the repository root:

``` powershell
python benchmarks/offshore/environmental_contour/run.py
```
