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

## Configured engineering workflow

`EngineeringAnalysisWorkflow` connects a loaded `OffshoreProject` to the
configured OpenFAST or HEROWIND adapter and then to one selected analysis. The
solver output may be declared as `solver.output_file` or supplied explicitly to
`run()`.

``` python
from offshoresafe import EngineeringAnalysisWorkflow, OffshoreProject

project = OffshoreProject.load("path/to/project.yaml")
workflow = EngineeringAnalysisWorkflow(project)
result = workflow.run("tower-extreme")
workflow.export_result(result, "build/tower-extreme.json")
```

The immutable result records project, analysis, solver, adapter, OffshoreSafe
version, UTC timestamp, processing parameters, input/output metadata and hashes,
and the analysis payload. `EngineeringAnalysisResult.load()` restores an
exported JSON result. Export uses stable key ordering, so repeated exports of
the same result object are byte-identical.

Supported analysis settings:

| Analysis type | Settings |
| --- | --- |
| `statistics` | optional `channels`, optional `ddof` |
| `extreme` | required `channel` and `return_period`; optional `direction`, `threshold`, `min_distance`, `distribution`, and `events_per_period` |
| `fatigue` | required `channel`, `slope`, `log10_intercept`, and `equivalent_cycles`; optional `endurance_limit` |
| `tower_reliability` | required `channel` and material/geometry/load `variables`; optional load statistic, correlation, design factors, and UQRA `solver_options` |

Unknown analysis types and settings fail explicitly. Solver-specific parsing
remains in adapters; the post-processing functions consume only normalized
`SolverResult` objects.
The tower reliability method is documented separately in
`docs/tower_reliability.md`.

Verification:

```console
python -m pytest -q tests/offshoresafe/test_extreme.py
python -m pytest -q tests/offshoresafe/test_fatigue.py
python -m pytest -q tests/offshoresafe/test_engineering_workflow.py
python benchmarks/offshore/extreme_response/run.py
python benchmarks/offshore/fatigue/run.py
python benchmarks/offshore/engineering_workflow/run.py
```
