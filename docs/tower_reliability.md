# Tower Reliability

Issue #070 is the first OffshoreSafe structural reliability vertical slice. It
uses normalized solver loads, defines the engineering limit state in
OffshoreSafe, and delegates probability transformations and reliability solving
to UQRA.

## Bending limit state

The implemented tower-base bending safety margin is

``` text
g(X) = fy * Z * 1000 / gamma_m - Mref * L * gamma_f
```

where:

| Symbol | Meaning | Expected unit |
| --- | --- | --- |
| `fy` | Yield strength | MPa |
| `Z` | Tower section modulus at the assessed section | m^3 |
| `Mref` | Reference moment selected from a normalized solver channel | kN-m |
| `L` | Stochastic load multiplier | dimensionless |
| `gamma_m` | Deterministic material factor | dimensionless |
| `gamma_f` | Deterministic load factor | dimensionless |

The factor 1000 converts `MPa * m^3` to `kN-m`. Positive margin is safe and
zero or negative margin is failure. The available load statistics are
`maximum`, `minimum` (absolute magnitude of the minimum), and
`maximum_absolute`.

## Project configuration

``` yaml
- analysis_id: tower-form
  analysis_type: tower_reliability
  method: FORM
  backend: native
  settings:
    channel: tower_base_fore_aft_moment
    load_statistic: maximum_absolute
    material_factor: 1.0
    load_factor_design: 1.0
    variables:
      yield_strength:
        distribution: Normal
        parameters: {mean: 355.0, std: 17.75}
        unit: MPa
      section_modulus:
        distribution: Normal
        parameters: {mean: 0.1, std: 0.005}
        unit: m^3
      load_factor:
        distribution: Normal
        parameters: {mean: 1.0, std: 0.05}
    correlation_matrix:
      - [1.0, 0.0, 0.0]
      - [0.0, 1.0, 0.0]
      - [0.0, 0.0, 1.0]
```

`solver_options` is passed to the selected UQRA reliability backend. For
example, native Monte Carlo accepts `n_samples`, `random_state`, and
`confidence_level`; native FORM accepts `initial_point`, `tolerance`, and
`max_iterations`.

## Result

The normal `EngineeringAnalysisResult` provenance is retained. Its payload adds:

-   reference channel, unit, statistic, and moment;
-   material and load design factors;
-   ordered variable definitions and correlation matrix;
-   failure probability and reliability index;
-   confidence interval when provided by the solver;
-   physical and standard-normal design points;
-   sensitivity direction, convergence, iterations, and backend metadata.

## Scope and limitations

-   This is a bending-resistance screening model, not a complete tower code
    check.
-   The caller is responsible for deriving a valid section modulus and selecting
    representative solver channels and load statistics.
-   Buckling, shell interaction, weld details, stress concentration, fatigue,
    partial-factor code calibration, and multi-axial interaction are not implicit.
-   Normal variables can mathematically sample nonphysical negative values;
    distributions and parameters must be selected for the engineering case.
-   The current fixture is a small analytical verification case, not a certified
    turbine design assessment.

## Verification

``` powershell
python -m pytest -q tests/offshoresafe/test_tower_reliability.py
python benchmarks/offshore/tower_reliability/run.py
```
