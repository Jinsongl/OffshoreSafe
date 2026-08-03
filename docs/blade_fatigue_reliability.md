# Blade Fatigue Reliability

Issue #071 connects normalized blade-root load histories, OffshoreSafe rainflow
counting, an uncertain S-N damage model, and UQRA reliability solvers.

## Limit state

For rainflow ranges `S_i` and counts `n_i`, the implemented lifetime damage is

``` text
D(X) = B * sum(n_i * (L * S_i)^m) / 10^a
g(X) = D_limit - D(X)
```

`L` is a positive stochastic load multiplier, `m` is the stochastic S-N slope,
`a` is the stochastic base-10 S-N intercept, and `B` is the deterministic number
of repetitions of the simulated cycle block. Positive margin is safe.

## Configuration

``` yaml
- analysis_id: blade-fatigue-form
  analysis_type: blade_fatigue_reliability
  method: FORM
  backend: native
  settings:
    channel: blade_1_root_flap_moment
    lifetime_repetitions: 50.0
    damage_limit: 1.0
    variables:
      load_factor:
        distribution: Lognormal
        parameters: {mean: 1.0, std: 0.05}
      sn_slope:
        distribution: Normal
        parameters: {mean: 3.0, std: 0.1}
      sn_log10_intercept:
        distribution: Normal
        parameters: {mean: 6.0, std: 0.1}
```

The load factor is Lognormal so sampled load scaling remains positive. The S-N
slope and intercept currently use Normal distributions. An optional
`correlation_matrix` follows the variable order shown above. `solver_options`
is passed to the selected UQRA reliability backend.

## Result

The Issue #064 result envelope retains project and solver provenance. The blade
payload adds:

-   canonical load channel and unit;
-   rainflow ranges, means, and half/full counts;
-   reference damage evaluated at arithmetic variable means;
-   lifetime repetitions and damage limit;
-   variable definitions and correlation matrix;
-   failure probability, reliability index, design points, sensitivity,
    convergence, and backend metadata.

## Scope and limitations

-   The input cycle block and `lifetime_repetitions` must represent the intended
    operating-life exposure; the software does not infer lifetime occurrence.
-   No mean-stress correction, thickness correction, environmental degradation,
    partial safety factor, or IEC/DNV code rule is implicit.
-   The load multiplier scales every rainflow range uniformly. Separate wind,
    turbulence, control, and model uncertainties require a richer response model.
-   Miner linear accumulation and the single-slope power law are modeling
    assumptions, not universally valid material behavior.
-   The benchmark is an analytical software-verification case, not a certified
    blade design assessment.

## Verification

``` powershell
python -m pytest -q tests/offshoresafe/test_blade_fatigue_reliability.py
python benchmarks/offshore/blade_fatigue_reliability/run.py
```
