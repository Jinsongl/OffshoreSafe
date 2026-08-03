# UQRA Plugin Compatibility Matrix

This document is the installation and compatibility reference for the optional
algorithm backends registered by UQRA. Core UQRA requires only NumPy and SciPy;
importing `uqra` does not import any package in this table.

| Backend | Extra | Capabilities | Result contract | Numerical dependency |
|---|---|---|---|---|
| `native` | core | MC/LHS/Sobol sampling; MC/FORM/SORM reliability | `SamplingResult`, `ReliabilityResult` | NumPy/SciPy |
| `openturns` | `openturns` | distribution conversion; FORM/SORM | `ReliabilityResult` | OpenTURNS 1.25+ |
| `uqpy` | `uqpy` | MC/LHS sampling; FORM/SORM | `SamplingResult`, `ReliabilityResult` | UQpy 4.2; NumPy 1.26; `setuptools<81` |
| `chaospy` | `chaospy` | quadrature/regression PCE | `SurrogateResult` | Chaospy 4.3.21+; numpoly 1.3.9+; NumPy 2 |
| `salib` | `salib` | Sobol indices; Morris screening | `SensitivityResult` | SALib 1.5.2+; NumPy 2 |

## Installation

Install core development dependencies:

``` powershell
python -m pip install -e ".[dev]"
```

Install one optional backend at a time:

``` powershell
python -m pip install -e ".[dev,openturns]"
python -m pip install -e ".[dev,uqpy]"
python -m pip install -e ".[dev,chaospy]"
python -m pip install -e ".[dev,salib]"
```

UQpy and the current Chaospy/SALib stack have incompatible NumPy requirements.
They must use separate environments. The GitHub Actions jobs in
`.github/workflows/quality.yml` enforce this isolation.

## Discovery and failure behavior

All adapters are registered even when their dependency is not installed. This
allows stable backend names and capability inspection:

``` python
from uqra import available_backends, get_backend

print(available_backends())
print(get_backend("salib").capabilities)
```

Calling an unavailable adapter raises a `RuntimeError` containing the matching
installation extra. The native backend remains usable. Discovery helpers such
as `openturns_available()` and `salib_available()` do not import the optional
runtime.

## Verification commands

Core verification:

``` powershell
python -m pytest -q
ruff check packages tests benchmarks
ruff format --check packages tests benchmarks
```

Optional jobs set one marker environment variable and run one benchmark:

| Backend | Test variable and marker | Benchmark |
|---|---|---|
| OpenTURNS | `UQRA_TEST_OPENTURNS=1`, `-m openturns` | `benchmarks/mathematical/openturns_backend/run.py` |
| UQpy | `UQRA_TEST_UQPY=1`, `-m uqpy` | `benchmarks/mathematical/uqpy_backend/run.py` |
| Chaospy | `UQRA_TEST_CHAOSPY=1`, `-m chaospy` | `benchmarks/mathematical/chaospy_backend/run.py` |
| SALib | `UQRA_TEST_SALIB=1`, `-m salib` | `benchmarks/mathematical/salib_backend/run.py` |

## Supported input limits

- OpenTURNS supports the documented marginal conversions and Gaussian-copula
  correlation.
- UQpy supports Normal, Lognormal, and Uniform marginals; UQpy 4.2 does not
  expose Weibull.
- Chaospy PCE currently requires independent variables.
- SALib conversion currently requires independent Uniform variables. An
  explicit SALib problem mapping may also be supplied.

These restrictions are represented by capability declarations or explicit
validation errors; adapters do not silently approximate unsupported inputs.
