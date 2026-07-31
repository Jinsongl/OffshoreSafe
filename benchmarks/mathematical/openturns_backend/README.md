# OpenTURNS Backend Benchmark

This optional Issue #041 benchmark compares UQRA native and OpenTURNS FORM and
SORM results. It also verifies Gaussian-copula correlation conversion.

Install the optional backend and run:

``` powershell
python -m pip install -e ".[openturns]"
python benchmarks/mathematical/openturns_backend/run.py
```

The OpenTURNS package is not required by the UQRA core or native CI job.
