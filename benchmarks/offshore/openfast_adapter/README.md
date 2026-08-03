# OpenFAST Adapter Benchmark

This deterministic Issue #052 fixture uses a minimal OpenFAST-style primary
input file and ASCII output table. It verifies version and scalar input parsing,
canonical channel mapping, unit extraction, time-series preservation, and a
known tower-base moment.

No OpenFAST executable or third-party parser is required:

```console
python benchmarks/offshore/openfast_adapter/run.py
```
