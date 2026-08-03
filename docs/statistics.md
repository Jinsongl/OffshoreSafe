# Channel Statistics

Issue #060 adds deterministic descriptive statistics for normalized
`SolverResult` channels. The implementation belongs to OffshoreSafe engineering
post-processing; UQRA remains unchanged.

```python
from offshoresafe import compute_statistics

statistics = compute_statistics(solver_result)
tower = statistics["tower_base_fore_aft_moment"]
print(tower.mean, tower.maximum, tower.rms)
```

Each `ChannelStatistics` contains sample count, mean, standard deviation,
minimum, maximum, RMS, and the source unit. `ddof=0` is the default and computes
population standard deviation. Pass `ddof=1` for sample standard deviation.
Only named channels may be selected, selection order is preserved, and duplicate
or unknown names are rejected.

`StatisticsResult` and its mappings are immutable. Its metadata carries forward
the solver adapter, file hashes, and other source traceability fields, and adds
`processing_method=channel_statistics`, `ddof`, and sample count. Non-finite or
empty input cannot enter through the validated `SolverResult` contract.

Verification:

```console
python -m pytest -q tests/offshoresafe/test_statistics.py
python benchmarks/offshore/statistics/run.py
```
