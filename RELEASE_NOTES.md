# OffshoreSafe 0.1.0

OffshoreSafe 0.1.0 is the first frozen engineering MVP.

## Delivered

- Versioned `project.yaml` workflows through normalized solver results,
  post-processing, fatigue, and structural reliability.
- OpenFAST ASCII and HEROWIND text-result adapters.
- Tower, blade-fatigue, floating-platform, and IFORM environmental-contour
  reference cases with deterministic acceptance.
- Unified traceability manifests with source-file hash verification.
- Template v1.1 Markdown, Excel, and PDF engineering reports.

## Compatibility and deferred scope

Python 3.11 or newer and UQRA 0.1 prerelease are required. PDF output requires
`offshoresafe[reports]`. Bladed, OrcaFlex, advanced design-code cases,
surrogates, Bayesian calibration, HPC, dashboards, and electronic approvals
are deferred. See `docs/mvp_release.md` for full verification and limitations.
