# Engineering Post-processing

Milestone 2.1 belongs entirely to the OffshoreSafe engineering layer and
operates on normalized solver time series. UQRA and the architecture are
unchanged.

## Extreme response

`extract_peaks()` finds interior local maxima, minima, or absolute peaks. A
threshold and integer sample separation can suppress small or closely spaced
events. Returned indices, times, signed values, units, and solver traceability
are immutable.

`fit_extreme_distribution()` fits either a Gumbel maximum distribution or a
positive two-parameter Weibull distribution by maximum likelihood.
`return_period_response()` evaluates the non-exceedance probability
`1 - 1 / (T n)`, where `T` is the return period and `n` is the number of
independent extreme events per period. Independence and stationarity are
engineering assumptions that callers must establish for their data.

## Rainflow and fatigue

`count_rainflow()` reduces a finite load sequence to reversals and applies the
ASTM E1049 four-point procedure. It returns each load range, cycle mean, and
half/full count; retaining half cycles makes sequence residue explicit.

`SNCurve` implements the power law `N = 10^a / S^m`, with optional endurance
limit. `calculate_fatigue_damage()` applies Miner's linear accumulation rule.
No mean-stress correction is implicit: apply any required Goodman or other
correction before constructing cycles for damage evaluation.

`calculate_del()` computes
`(sum(n_i S_i^m) / N_eq)^(1/m)`. Load units follow the input ranges.

Verification:

```console
python -m pytest -q tests/offshoresafe/test_extreme.py
python -m pytest -q tests/offshoresafe/test_fatigue.py
python benchmarks/offshore/extreme_response/run.py
python benchmarks/offshore/fatigue/run.py
```
