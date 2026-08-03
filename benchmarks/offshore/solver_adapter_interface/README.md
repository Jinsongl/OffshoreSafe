# Solver Adapter Interface Benchmark

This Issue #051 compatibility benchmark constructs a normalized, immutable
two-channel solver result with 10,001 samples. It verifies sample preservation,
canonical channel order, and a known final response value without requiring an
external engineering solver.

Run from the repository root:

```console
python benchmarks/offshore/solver_adapter_interface/run.py
```
