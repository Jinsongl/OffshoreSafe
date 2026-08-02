# Chaospy Backend Benchmark

This optional Issue #043 benchmark verifies exact quadrature and regression
PCE recovery of a quadratic model, then compares Ishigami PCE mean and variance
with analytical values.

``` powershell
python -m pip install -e ".[chaospy]"
python benchmarks/mathematical/chaospy_backend/run.py
```

Chaospy and numpoly are not required by the UQRA core or native CI job.
