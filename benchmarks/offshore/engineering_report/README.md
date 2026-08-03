# Unified traceability and engineering report benchmark

This benchmark runs the tower, blade-fatigue, and floating-platform vertical
cases through the project-to-solver workflow. Each case applies an explicit
benchmark reliability target, verifies the normalized traceability manifest
and current source-file hashes, and exports Markdown, Excel, PDF, and standalone
manifest JSON artifacts from the same result object.

Run from the repository root with the report extra installed:

```text
python benchmarks/offshore/engineering_report/run.py
```

Artifacts are written to the format-specific `output/reports/`,
`output/spreadsheets/`, `output/pdf/`, and `output/manifests/` directories.
