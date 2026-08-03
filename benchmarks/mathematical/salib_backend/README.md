# SALib Backend Benchmark

This optional Issue #044 benchmark compares Ishigami Sobol first- and
total-order indices with analytical values. It also verifies Morris screening
ranking and fixed-seed reproducibility on a weighted linear model.

``` powershell
python -m pip install -e ".[salib]"
python benchmarks/mathematical/salib_backend/run.py
```

SALib is not required by the UQRA core or native CI job.
