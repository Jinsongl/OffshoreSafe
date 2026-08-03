# Solver Adapter Interface

Issue #051 defines the boundary between OffshoreSafe and external engineering
solvers. Solver-specific file formats and channel names remain inside concrete
adapters; downstream workflows receive only a normalized `SolverResult`.

## Contract

Every concrete adapter derives from `SolverAdapter` and implements:

- `read_input(path)` for solver input metadata;
- `read_output(path)` for normalized time-series data;
- `map_channel(source_name)` for one solver-to-canonical name mapping;
- `export_result(result, path)` for a portable result representation.

The base class provides channel pass-through for names not present in an
adapter's `channel_map`. `SolverCapability` and `supports()` allow callers to
inspect these operations without executing or importing a solver SDK.

## Normalized result

`SolverResult` contains strictly increasing finite time values, one or more
finite channels of equal length, optional units, and adapter metadata. It copies
sequences into tuples and exposes read-only mappings to prevent parser buffers
from changing a completed result.

```python
from offshoresafe import SolverResult

result = SolverResult(
    time=[0.0, 0.1, 0.2],
    channels={"tower_base_moment": [100.0, 102.0, 101.0]},
    units={"tower_base_moment": "kN m"},
    metadata={"adapter": "example", "solver_version": "1.0"},
)
```

Concrete OpenFAST, HEROWIND, Bladed, and OrcaFlex adapters are separate
features. The interface does not import their Python SDKs or encode their file
formats. Solver execution is likewise outside the minimal Issue #051 parsing
and normalization contract.

Issue #052 implements the first concrete integration, `OpenFASTAdapter`, for
primary input metadata and ASCII output. See `openfast_adapter.md` for its
format boundary and canonical channel set.

Issue #053 adds `HEROWINDAdapter` with the same canonical channel vocabulary;
see `herowind_adapter.md`.

## Verification

Run the contract tests and compatibility benchmark from the repository root:

```console
python -m pytest -q tests/offshoresafe/test_solver_adapter.py
python benchmarks/offshore/solver_adapter_interface/run.py
```
