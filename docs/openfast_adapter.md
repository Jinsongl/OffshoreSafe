# OpenFAST Adapter

Issue #052 provides a dependency-free `OpenFASTAdapter` for OpenFAST primary
input files and whitespace-delimited ASCII `.out` time series. The adapter is an
OffshoreSafe engineering integration and does not add OpenFAST concepts to UQRA.

## Supported data

`read_input()` extracts scalar primary-file parameters, the OpenFAST version,
the resolved source path, and a SHA-256 input hash. Quoted strings, booleans,
integers, decimal values, and Fortran `D` exponents are normalized to Python
values.

`read_output()` locates the `Time` and units rows rather than depending on a
fixed header length. It validates every data row, accepts `D` exponents, and
returns `SolverResult` with source-file hash, source channel names, version,
units, and canonical channels. The initial mapping covers wind speed, rotor and
generator quantities, blade-root moments, tower-base moments, and platform
motions. Unknown channels pass through unchanged so data is not silently lost.

```python
from offshoresafe import OpenFASTAdapter

adapter = OpenFASTAdapter()
inputs = adapter.read_input("main.fst")
result = adapter.read_output("main.out")
adapter.export_result(result, "build/main.normalized.json")
```

Binary `.outb` parsing is not part of Issue #052. Passing an `.outb` path raises
a clear error instructing the caller to request ASCII `.out` output. This avoids
an undeclared dependency on a third-party OpenFAST parser.

## Verification

The checked-in fixture and expected result are independent of an OpenFAST
installation:

```console
python -m pytest -q tests/offshoresafe/test_openfast_adapter.py
python benchmarks/offshore/openfast_adapter/run.py
```
