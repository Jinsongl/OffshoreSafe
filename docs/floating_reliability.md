# Floating-platform Reliability

Issue #072 connects normalized platform motion or mooring tension to uncertain
Hs, Tp, current speed, mooring stiffness, and UQRA reliability solvers.

The screening response model is:

``` text
R(X) = Rref (Hs/Hs_ref)^p (Tp/Tp_ref)^q
            (U/U_ref)^r (K_ref/K)^s
g(X) = Rlim - R(X)
```

All four variables must use positive Lognormal or Weibull marginals. The default
exponents are `(2, 1, 1, 1)`. Configuration selects `platform_motion` or
`mooring_tension`, a normalized response channel, reference environment,
response limit, variables, optional correlation, optional exponents, and UQRA
solver options.

The Issue #064 envelope retains solver hashes and project provenance. The
payload includes reference response, limit, environment, exponents, variable
definitions, correlation, `pf`, `beta`, design points, sensitivity, convergence,
and backend metadata.

## Limitations

-   This explicit power-law surface is a software-verification and screening
    model, not a hydrodynamic, aero-servo-elastic, or mooring solver.
-   Exponents and reference conditions require calibration against simulations
    or measurements before engineering use.
-   Resonance, directionality, nonlinear mooring geometry, line dynamics,
    multi-body coupling, and extreme-event sequencing are not implicit.
-   A single response channel and scalar limit are assessed per analysis.

## Verification

``` powershell
python -m pytest -q tests/offshoresafe/test_floating_reliability.py
python benchmarks/offshore/floating_reliability/run.py
```
