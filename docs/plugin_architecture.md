# Plugin Architecture Design

## 1. Objective

UQRA adopts a plugin-based architecture to integrate mature uncertainty
quantification and reliability software.

The goal is:

-   keep UQRA core lightweight and domain-independent;
-   reuse mature algorithms;
-   provide unified APIs;
-   allow different computational backends.

Architecture:

    OffshoreSafe
          |
          v
        UQRA Core
          |
          v
    Plugin Backend Layer

    OpenTURNS
    FERUM
    UQpy
    Chaospy
    SALib
    PyMC
    emcee
    Tasmanian

------------------------------------------------------------------------

## 2. Design Principle

UQRA Core defines:

-   data structures;
-   problem definitions;
-   workflow interfaces;
-   result formats.

Plugins provide:

-   numerical algorithms;
-   external solver calls;
-   specialized methods.

The user should not depend on a specific backend.

Example:

``` python
result = uqra.reliability.solve(
    method="FORM",
    backend="OpenTURNS"
)
```

------------------------------------------------------------------------

## 3. Plugin Categories

## 3.1 Reliability Backend

Functions:

-   FORM
-   SORM
-   Monte Carlo reliability
-   Importance sampling
-   Subset simulation

Interface:

``` python
from uqra import ReliabilityBackend

class ExampleBackend(ReliabilityBackend):
    name = "example"
    capabilities = frozenset(...)

    def solve_reliability(self, problem, method, **options):
        ...
```

Candidates:

-   OpenTURNS
-   FERUM
-   UQpy

------------------------------------------------------------------------

## 3.2 Sampling Backend

Functions:

-   Monte Carlo
-   LHS
-   Sobol sequence
-   Sparse grid

Candidates:

-   Chaospy
-   UQpy
-   Tasmanian

------------------------------------------------------------------------

## 3.3 Sensitivity Backend

Functions:

-   Sobol indices
-   Morris method
-   variance decomposition

Candidate:

-   SALib

------------------------------------------------------------------------

## 3.4 Surrogate Backend

Functions:

-   Polynomial Chaos Expansion
-   Gaussian Process
-   Kriging
-   Sparse approximation

Candidates:

-   Chaospy
-   Tasmanian
-   scikit-learn

Issue #043 adds the minimal runtime contract:

``` python
class SurrogateBackend(Backend):
    def fit_surrogate(self, model, variables, method, **options): ...

result = get_backend("chaospy").fit_surrogate(model, variables, "PCE", order=3)
prediction = result.predict(samples)
```

`SurrogateResult` contains the method, a callable fitted surrogate, summary
statistics, and traceability metadata. `normalize_surrogate_result()` accepts
the same contract from external plugins.

------------------------------------------------------------------------

## 3.5 Bayesian Backend

Functions:

-   MCMC
-   Bayesian calibration
-   posterior estimation

Candidates:

-   PyMC
-   emcee

------------------------------------------------------------------------

# 4. Result Normalization

All plugins shall return unified UQRA objects.

Example:

    FORMResult

        probability_failure

        reliability_index

        design_point

        sensitivity

        backend_information

The user should not need to know whether the calculation was performed
by OpenTURNS or native UQRA.

Issue #040 provides `normalize_reliability_result()`,
`normalize_sampling_result()`, and `normalize_sensitivity_result()` for this
boundary. Adapters may return an existing UQRA result object or a mapping with
the documented canonical fields.

------------------------------------------------------------------------

# 4.1 Capability Discovery and Registration

Backend capabilities use stable identifiers such as `reliability.form`,
`sampling.sobol`, and `sensitivity.morris`:

``` python
from uqra import Capability, available_backends, get_backend

backend = get_backend("native")
assert backend.supports(Capability.RELIABILITY_FORM)
print(available_backends())
```

The built-in registry contains `native` with the alias `uqra`. Optional
adapters register explicitly through `backend_registry.register()`. Importing
UQRA does not import or require external backend packages.

------------------------------------------------------------------------

# 5. OpenTURNS Integration Strategy

Role:

Primary reliability and UQ backend.

Functions:

-   distribution;
-   transformation;
-   FORM;
-   SORM;
-   PCE;
-   sensitivity.

Integration:

    UQRA Problem

          |

    OpenTURNS Adapter

          |

    OpenTURNS API

Implemented Issue #041 scope:

-   optional installation through `pip install -e ".[openturns]"`;
-   lazy runtime import, so core UQRA does not require OpenTURNS;
-   Normal, arithmetic-moment Lognormal, Weibull, and Uniform conversion;
-   Gaussian-copula correlation conversion;
-   FORM and Breitung, Hohenbichler, and Tvedt SORM;
-   normalization to `ReliabilityResult` with backend name, version,
    algorithm, correction, and optimizer metadata.

The backend is registered under `openturns`. If the optional package is not
installed, discovery remains available but execution raises an installation
message without affecting the native backend.

------------------------------------------------------------------------

# 5.1 UQpy Integration Strategy

Issue #042 adds the optional `uqpy` backend without changing the native API:

-   install with `pip install -e ".[uqpy]"`;
-   lazy runtime import, including an actionable error for incomplete installs;
-   Normal, arithmetic-moment Lognormal, and Uniform conversion;
-   unit-hypercube Monte Carlo and Latin hypercube sampling;
-   FORM with Gaussian correlation and Breitung SORM;
-   normalized `SamplingResult` and `ReliabilityResult` metadata containing
    backend, UQpy version, and algorithm name.

UQpy 4.2 does not expose a Weibull marginal, so the adapter does not advertise
that capability. Its legacy `pkg_resources` import requires `setuptools<81`,
which is isolated in the `uqpy` optional extra. Core installation and import do
not load UQpy or PyTorch.

------------------------------------------------------------------------

# 5.2 Chaospy Integration Strategy

Issue #043 registers the optional `chaospy` backend and supports:

-   Normal, arithmetic-moment Lognormal, Weibull, and Uniform conversion;
-   independent joint distributions for polynomial chaos;
-   orthonormal polynomial basis generation;
-   Gaussian quadrature/spectral projection and Sobol point regression;
-   scalar or vector model evaluation and surrogate prediction;
-   analytical PCE mean, variance, and standard deviation;
-   normalized metadata including version, order, basis size, fitting method,
    rule, and training sample count.

Install with `pip install -e ".[chaospy]"`. Current numpoly releases require
NumPy 2, while UQpy 4.2 fixes NumPy 1.26; therefore these optional backends use
separate CI jobs and are never co-installed in the core environment. Correlated
PCE is outside the first-stage contract and is rejected explicitly.

------------------------------------------------------------------------

# 6. FERUM Integration Strategy

FERUM is treated as:

-   structural reliability reference;
-   benchmark source;
-   optional MATLAB backend.

Initial strategy:

1.  reproduce classical FERUM examples;
2.  compare UQRA results;
3.  migrate useful algorithms gradually.

FERUM is not a runtime dependency.

------------------------------------------------------------------------

# 7. Plugin Development Rules

Every plugin requires:

    plugin_name/

    adapter.py

    capability.yaml

    tests/

    examples/

    README.md

Requirements:

1.  Unified API.
2.  Independent dependency.
3.  Automatic capability detection.
4.  Benchmark validation.
5.  Version compatibility record.

------------------------------------------------------------------------

# 8. Long-term Strategy

Initial stage:

Integrate existing mature tools.

Middle stage:

Replace critical functions with native UQRA implementations.

Long term:

UQRA becomes an independent reliability framework.
