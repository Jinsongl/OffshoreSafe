# HEROWIND Adapter

Issue #053 implements `HEROWINDAdapter` for the text result convention verified
against the HEROWIND source and archived `MultibodyOutput.txt`: a comma-separated
channel header followed by whitespace- or comma-separated numeric rows.

`read_output()` requires `time` as the first field, extracts optional units from
`Channel (unit)` headers, accepts Fortran `D` exponents, maps OpenFAST-compatible
HEROWIND channel names to the same canonical OffshoreSafe vocabulary, and keeps
unknown channels unchanged. Metadata includes source channels, path, format, and
SHA-256 hash. `read_input()` loads HEROWIND YAML configuration and records its
hash; `export_result()` writes normalized JSON.

```python
from offshoresafe import HEROWINDAdapter

adapter = HEROWINDAdapter()
configuration = adapter.read_input("case.yaml")
result = adapter.read_output("MultibodyOutput.txt")
adapter.export_result(result, "build/result.json")
```

Run `python benchmarks/offshore/herowind_adapter/run.py` for the deterministic
fixture benchmark.
