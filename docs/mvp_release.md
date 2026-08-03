# OffshoreSafe MVP 0.1.0 Release Baseline

## Frozen scope

OffshoreSafe 0.1.0 freezes the public imports exported by `offshoresafe`, the
`EngineeringAnalysisResult` schema at `1.0`, and the engineering report template
at `1.1`. No algorithms, solver integrations, or report fields are added after
this baseline. Post-release work is limited to severe defects until a new
version scope is approved.

## Clean-environment installation

Use Python 3.11 or newer from the repository root:

``` powershell
python -m pip install -e ".[dev]"
python -m pip install -e "packages/offshoresafe[reports]"
python -c "import uqra, offshoresafe; print(uqra.__version__, offshoresafe.__version__)"
```

## Release verification

``` powershell
python -m pytest -q
ruff check .
ruff format --check .
python benchmarks/offshore/engineering_report/run.py
python benchmarks/offshore/environmental_contour/run.py
```

The first acceptance command runs the tower, blade-fatigue, and floating
project workflows. The second runs the environmental contour. Every case has
fixed repository input, fixed numerical references, explicit PASS/FAIL
criteria, a complete traceability manifest, and template v1.1 Markdown, Excel,
and PDF reports. Generated artifacts under `output/` are not versioned.

## Acceptance matrix

| Chain | Fixed input | Acceptance |
| --- | --- | --- |
| Tower reliability | `tower_reliability/input/project.yaml` | beta >= 3.0; complete manifest |
| Blade fatigue | `blade_fatigue_reliability/input/project.yaml` | beta >= 1.0; complete manifest |
| Floating platform | `floating_reliability/input/project.yaml` | beta >= 2.5; complete manifest |
| Environmental contour | `environmental_contour/input.yaml` and `expected_result.yaml` | 50-year IFORM radius/reference point; complete manifest |

Any failed numerical assertion, FAIL report status, incomplete manifest, or
source-file hash mismatch blocks release.

## Known limitations

- OpenFAST supports ASCII results; execution and binary output are outside MVP.
- HEROWIND supports the verified text-result convention only.
- Bladed and OrcaFlex adapters are not implemented.
- Criteria are project-supplied; no design-code threshold is implied.
- PDF reports require the optional `reports` dependency.
- Reference cases demonstrate reproducibility, not project certification.

## Post-MVP candidates

Bladed and OrcaFlex adapters, additional design-code cases, surrogate
acceleration, Bayesian calibration, HPC orchestration, dashboards, and
electronic approvals require a separately approved release scope.
