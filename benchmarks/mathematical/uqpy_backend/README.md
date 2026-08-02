# UQpy Backend Benchmark

This optional Issue #042 benchmark compares UQRA native and UQpy FORM/SORM
results, checks correlated Gaussian input, and validates Latin hypercube strata.

``` powershell
python -m pip install -e ".[uqpy]"
python benchmarks/mathematical/uqpy_backend/run.py
```

UQpy is not required by the UQRA core or native CI job.
