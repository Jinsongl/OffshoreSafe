# Engineering Analysis Workflow Benchmark

This deterministic Issue #064 fixture loads a versioned OffshoreSafe project,
normalizes an OpenFAST ASCII result, and executes statistics, Gumbel extreme
response, rainflow/Miner fatigue damage, and DEL. It checks analytical or fixed
SciPy reference values together with input and output traceability hashes.

Run from the repository root:

``` powershell
python benchmarks/offshore/engineering_workflow/run.py
```
