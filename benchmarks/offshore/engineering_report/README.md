# Unified traceability and engineering report benchmark

This Issue #090/#091 benchmark loads the existing project-to-solver engineering
workflow result, attaches case/sample context, verifies the normalized
traceability manifest, and exports Markdown, Excel, and PDF reports from the
same result object.

Run from the repository root with the report extra installed:

```text
python benchmarks/offshore/engineering_report/run.py
```

Artifacts are written to the format-specific `output/reports/`,
`output/spreadsheets/`, and `output/pdf/` directories.
