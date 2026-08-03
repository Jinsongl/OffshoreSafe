# GitHub Issue Plan

Last reviewed: 2026-08-03

Review baseline includes the Issue #064 engineering workflow and Issue #070
tower reliability vertical slice.

Status legend:

-   **Complete**: implementation, public API, tests, benchmark, and documentation
    are present unless noted otherwise.
-   **Planned**: approved scope has not been implemented.
-   **Deferred**: intentionally postponed and not part of the immediate critical
    path.

## 1. Purpose

This document converts the development roadmap into GitHub Milestones
and Issues.

Each issue should include:

-   background;
-   implementation scope;
-   API impact;
-   tests;
-   benchmark;
-   acceptance criteria.

The plan is designed for:

-   GitHub issue management;
-   Codex-assisted development;
-   incremental software delivery.

## 1.1 Current Delivery Snapshot

| Milestone | Status | Delivered |
| --- | --- | --- |
| 0.1 Repository Foundation | Complete | Packaging, versioning, pytest, Ruff, and CI |
| 0.2 UQRA Core Data Model | Complete | Random variables, distributions, random vectors, and correlation handling |
| 0.3 Sampling Engine | Complete | Monte Carlo, Latin hypercube, and Sobol sampling |
| 0.4 Reliability Engine | Complete | Limit states, Monte Carlo reliability, FORM, and SORM |
| 1.0 UQRA Alpha | Complete | `v0.1.0a1` release candidate and stable Alpha public API |
| 1.1 Plugin Architecture | Complete | Native, OpenTURNS, UQpy, Chaospy, and SALib backends |
| 2.0 OffshoreSafe MVP: solver integration | Partially complete | Project schema, solver contract, OpenFAST ASCII, and HEROWIND text adapters; Bladed deferred |
| 2.1 Engineering Post Processing | Complete | Statistics, extremes, rainflow, Miner damage, S-N curves, DEL, and the configured analysis workflow |
| 2.2 Offshore Reliability | Partially complete | Tower-base bending and blade-fatigue reliability complete; floating-platform workflow planned |
| 3.0 Environmental Contour | Planned | Metocean model and IFORM contour |
| 4.0 Reporting and Traceability | Planned | End-to-end provenance and engineering reports |

Current verification baseline:

-   151 tests pass in the `offshoresafe-dev` Python 3.11 environment.
-   37 optional-backend tests are skipped when their third-party packages are
    not installed.
-   Ruff lint and format checks pass.
-   The blade-fatigue-reliability, tower-reliability, engineering-workflow,
    extreme-response, and fatigue benchmarks pass.

The architectural boundary remains intact: OffshoreSafe depends on UQRA, while
UQRA contains no offshore engineering or solver-specific imports.

## 1.2 Issue Status Index

| Issues | Status | Evidence summary |
| --- | --- | --- |
| #001--#003 | Complete | Repository layout, package manifests, tests, and CI workflows |
| #010--#012 | Complete | `uqra.core` implementation and probability-model tests |
| #020--#022 | Complete | Sampling implementations, statistical tests, and Ishigami benchmark |
| #030--#033 | Complete | Native reliability solvers and R-S/Four Branch/SORM benchmarks |
| #040--#044 | Complete | Backend contracts, adapters, compatibility matrix, and isolated optional tests |
| #050--#053 | Complete | OffshoreSafe project schema, solver result contract, OpenFAST, and HEROWIND adapters |
| #054 | Deferred | Bladed PRJ and result formats postponed by project decision |
| #060--#063 | Complete | Engineering statistics, extremes, rainflow, fatigue damage, and DEL |
| #064 | Complete in `15e4c44` | End-to-end engineering analysis orchestration, result provenance, and deterministic JSON |
| #070 | Complete | Tower-base bending reliability through normalized solver results and UQRA FORM/Monte Carlo |
| #071 | Complete | Blade-root fatigue reliability using rainflow, uncertain load/S-N parameters, and UQRA FORM/Monte Carlo |
| #072 | Planned | Floating-platform reliability workflow |
| #080--#081 | Planned | Metocean probability model and IFORM contour |
| #090--#091 | Planned | Cross-workflow traceability and report generation |

------------------------------------------------------------------------

# Milestone 0.1 --- Repository Foundation

## Issue #001 Repository Structure

Objective:

Create the initial repository structure.

Structure:

    src/
    tests/
    examples/
    benchmarks/
    docs/

Acceptance:

-   Python package can be imported.
-   Test framework runs successfully.
-   Documentation structure exists.

------------------------------------------------------------------------

## Issue #002 Python Package Setup

Tasks:

-   Create pyproject.toml.
-   Configure dependencies.
-   Configure version management.

Acceptance:

``` bash
pip install -e .
python -c "import uqra"
```

------------------------------------------------------------------------

## Issue #003 CI Pipeline

Tasks:

-   Configure GitHub Actions.
-   Add pytest workflow.
-   Add code quality checking.

------------------------------------------------------------------------

# Milestone 0.2 --- UQRA Core Data Model

## Issue #010 RandomVariable

Implement:

    RandomVariable

Properties:

-   name;
-   distribution;
-   parameters;
-   unit;
-   description.

Example:

``` python
X = RandomVariable(
    "E",
    "Normal",
    {"mean":210e9,"std":10e9}
)
```

Tests:

-   Normal distribution.
-   Lognormal distribution.
-   Weibull distribution.

------------------------------------------------------------------------

## Issue #011 Distribution Interface

Implement common interface:

    pdf()
    cdf()
    ppf()
    sample()

Initial distributions:

-   Normal;
-   Lognormal;
-   Weibull;
-   Uniform.

------------------------------------------------------------------------

## Issue #012 RandomVector

Support:

-   multiple variables;
-   correlation matrix;
-   covariance;
-   copula extension.

Benchmark:

Gaussian correlated variables.

------------------------------------------------------------------------

# Milestone 0.3 --- Sampling Engine

## Issue #020 Monte Carlo Sampling

Implement:

    MonteCarloSampler

Output:

-   samples;
-   metadata.

Validation:

Statistical convergence test.

------------------------------------------------------------------------

## Issue #021 Latin Hypercube Sampling

Implement LHS.

Benchmark:

Ishigami function.

------------------------------------------------------------------------

## Issue #022 Sobol Sampling

Implement low-discrepancy sequence sampling.

------------------------------------------------------------------------

# Milestone 0.4 --- Reliability Engine

## Issue #030 LimitStateFunction

Implement:

    g(X)

Support:

-   analytical functions;
-   external simulation models.

------------------------------------------------------------------------

## Issue #031 Monte Carlo Reliability

Output:

    ReliabilityResult

    Pf
    Beta
    confidence interval

Benchmark:

R-S problem.

------------------------------------------------------------------------

## Issue #032 FORM

Implement:

-   Hasofer-Lind reliability method;
-   design point search.

Output:

-   reliability index beta;
-   failure probability;
-   design point.

Benchmarks:

-   R-S problem;
-   Four Branch Function.

------------------------------------------------------------------------

## Issue #033 SORM

Implement:

-   Breitung method;
-   Hohenbichler method;
-   Tvedt method.

Benchmark:

Nonlinear limit-state functions.

------------------------------------------------------------------------

# Milestone 1.0 --- UQRA Alpha Release

Deliver:

-   probability module;
-   sampling module;
-   reliability module;
-   benchmark suite;
-   documentation.

Release:

    UQRA 0.1 Alpha

------------------------------------------------------------------------

# Milestone 1.1 --- Plugin Architecture

## Issue #040 Backend Interface

Implement:

    ReliabilityBackend
    SamplingBackend
    SensitivityBackend

Requirements:

-   unified API;
-   capability detection;
-   result normalization.

------------------------------------------------------------------------

## Issue #041 OpenTURNS Adapter

Support:

-   distribution;
-   FORM;
-   SORM.

Requirement:

Convert OpenTURNS outputs into UQRA result objects.

------------------------------------------------------------------------

## Issue #042 UQpy Adapter

Support selected UQ algorithms.

------------------------------------------------------------------------

## Issue #043 Chaospy Adapter

Support:

-   Polynomial Chaos Expansion.

------------------------------------------------------------------------

## Issue #044 SALib Adapter

Support:

-   Sobol sensitivity;
-   Morris method.

------------------------------------------------------------------------

# Milestone 2.0 --- OffshoreSafe MVP

## Issue #050 Project Definition

Implement:

    project.yaml

Contains:

-   project information;
-   turbine information;
-   solver information;
-   analysis configuration.

------------------------------------------------------------------------

## Issue #051 Solver Adapter Interface

Implement:

    SolverAdapter

    read_input()

    read_output()

    map_channel()

    export_result()

------------------------------------------------------------------------

## Issue #052 OpenFAST Adapter

Support:

-   time series reading;
-   channel mapping;
-   metadata extraction.

------------------------------------------------------------------------

## Issue #053 HEROWIND Adapter

Support:

-   HEROWIND result files;
-   unified channel format.

------------------------------------------------------------------------

## Issue #054 Bladed Adapter

Status: **Deferred** by project decision.

Support:

-   PRJ files;
-   result channels.

------------------------------------------------------------------------

# Milestone 2.1 --- Engineering Post Processing

## Issue #060 Statistics

Status: **Complete** in commit `608ba94`.

Implement:

-   mean;
-   standard deviation;
-   maximum;
-   minimum;
-   RMS.

------------------------------------------------------------------------

## Issue #061 Extreme Response

Status: **Complete** in commit `c5f3fe6`.

Implement:

-   peak extraction;
-   extreme distribution fitting;
-   return period response.

------------------------------------------------------------------------

## Issue #062 Rainflow Counting

Status: **Complete** in commit `c5f3fe6`.

Implement:

-   cycle counting;
-   fatigue damage calculation.

------------------------------------------------------------------------

## Issue #063 DEL Calculation

Status: **Complete** in commit `c5f3fe6`.

Support:

-   S-N curves;
-   Miner rule;
-   damage equivalent load.

------------------------------------------------------------------------

## Issue #064 Engineering Analysis Workflow

Status: **Complete** in commit `15e4c44`.

Objective:

Connect the completed OffshoreSafe project, solver-result, and post-processing
APIs into one traceable application workflow without moving engineering logic
into UQRA.

Implement:

-   select an analysis from `project.yaml`;
-   select the configured solver adapter explicitly;
-   load a normalized `SolverResult`;
-   execute statistics, extreme-response, or fatigue analysis from configuration;
-   produce a common immutable engineering-analysis result envelope;
-   preserve project ID, analysis ID, solver metadata, source hashes, processing
    parameters, software version, and timestamp;
-   serialize results to a documented JSON representation.

API decision required before implementation:

-   define the analysis configuration fields and result envelope in
    `docs/api_design.md`;
-   keep orchestration in OffshoreSafe and reuse UQRA only for mathematical
    probability and reliability operations.

Tests:

-   one end-to-end OpenFAST fixture flow;
-   one end-to-end HEROWIND fixture flow;
-   configuration validation and unsupported-analysis errors;
-   traceability-field preservation;
-   deterministic serialization round trip.

Benchmark:

Run a small normalized time-series fixture through statistics, extremes, and
fatigue, checking fixed reference outputs and provenance.

Acceptance:

-   no solver-specific branch exists inside post-processing functions;
-   the same analysis configuration works with normalized OpenFAST and HEROWIND
    results;
-   all outputs contain the required provenance fields;
-   API documentation, tests, benchmark, and roadmap are updated.

------------------------------------------------------------------------

# Milestone 2.2 --- Offshore Reliability

## Issue #070 Tower Reliability

Status: **Complete**.

Workflow:

    Tower loads

    +

    Material uncertainty

    ↓

    Limit state

    ↓

    Reliability analysis

Output:

-   Pf;
-   beta;
-   design points and sensitivity direction;
-   convergence and backend metadata;
-   Issue #064 project, solver, source-hash, parameter, version, and timestamp
    provenance.

Implemented scope:

-   normalized tower-base moment selection by maximum, minimum magnitude, or
    maximum absolute value;
-   bending limit state `fy * Z * 1000 / gamma_m - Mref * L * gamma_f`;
-   explicit yield-strength, section-modulus, and load-factor random variables;
-   optional correlation matrix and deterministic design factors;
-   native UQRA FORM and Monte Carlo, with other compatible reliability backends
    available through the existing backend name;
-   deterministic OpenFAST fixture benchmark against a first-order analytical
    linearization and fixed FORM reference.

Limitations:

-   bending screening only; buckling, shell interaction, welds, multi-axial
    interaction, fatigue, and code calibration are not implicit;
-   the fixture is a numerical verification case, not a certified turbine design.

------------------------------------------------------------------------

## Issue #071 Blade Fatigue Reliability

Status: **Complete**.

Workflow:

    Wind uncertainty

    ↓

    Blade root moment

    ↓

    Fatigue damage

    ↓

    Reliability

Implemented scope:

-   normalized blade-root load channel and ASTM-style rainflow cycles;
-   lifetime cycle-block repetition and configurable damage limit;
-   positive Lognormal load multiplier plus uncertain Normal S-N slope and
    log10 intercept;
-   optional correlation matrix and UQRA solver options;
-   native FORM and Monte Carlo through the existing reliability API;
-   Issue #064 result provenance, design points, sensitivity, convergence, and
    backend metadata;
-   analytical Miner damage and fixed FORM benchmark.

Limitations:

-   lifetime occurrence is configured rather than inferred;
-   mean-stress, thickness, environmental degradation, partial-factor, and
    code-specific corrections are not implicit;
-   uniform load scaling and a single-slope S-N/Miner model are deliberate
    verification assumptions.

------------------------------------------------------------------------

## Issue #072 Floating Platform Reliability

Variables:

-   Hs;
-   Tp;
-   current;
-   mooring stiffness.

Responses:

-   motion;
-   mooring tension.

------------------------------------------------------------------------

# Milestone 3.0 --- Environmental Contour

## Issue #080 Metocean Random Model

Support:

-   wind;
-   wave;
-   current;
-   joint distribution.

------------------------------------------------------------------------

## Issue #081 IFORM Environmental Contour

Implement:

-   probability transformation;
-   contour generation;
-   return period cases.

Benchmark:

Hs-Tp environmental contour.

------------------------------------------------------------------------

# Milestone 4.0 --- Reporting and Traceability

## Issue #090 Traceability System

Record:

-   input hash;
-   output hash;
-   solver version;
-   case ID;
-   analysis method;
-   result.

------------------------------------------------------------------------

## Issue #091 Engineering Report

Output:

-   Markdown;
-   Excel;
-   PDF.

------------------------------------------------------------------------

# Milestone 5.0 --- Industrial Version

Advanced features:

-   parallel Monte Carlo;
-   surrogate acceleration;
-   Bayesian calibration;
-   reliability-based design optimization;
-   HPC execution.

------------------------------------------------------------------------

# Known Problems and Constraints

## Product and workflow gaps

-   Issue #064 provides the application-level result envelope and persistence
    contract. Issues #070 and #071 connect tower bending and blade fatigue
    reliability to that envelope; floating-platform reliability remains
    unimplemented.
-   OpenFAST support currently reads primary input metadata and ASCII output
    only. Binary output and solver execution are outside the adapter contract.
-   HEROWIND support is limited to the verified YAML input and
    comma-header/whitespace-data result convention.
-   Bladed integration is deferred; OrcaFlex and generic CSV adapters have not
    yet been assigned implementation issues.
-   The workflow has a built-in adapter registry for OpenFAST and HEROWIND.
    Third-party adapter discovery is not yet part of the application layer.

## Engineering-method limitations

-   Extreme-value fitting currently supports Gumbel maxima and positive
    two-parameter Weibull models. Independence, stationarity, event definition,
    and model suitability remain caller responsibilities.
-   Peak separation is expressed in sample indices rather than physical time.
-   Fatigue processing provides ASTM-style rainflow counting, a power-law S-N
    curve, Miner accumulation, and DEL. It does not apply an implicit mean-stress
    correction, thickness correction, safety factor, or code-specific design
    rule.
-   The tower model currently covers a single tower-base bending limit state.
    Floating-platform, mooring, buckling, shell-interaction, and combined tower
    limit states are not implemented.
-   Blade fatigue currently uses uniform stochastic scaling of one rainflow block
    and a single-slope S-N/Miner model; richer wind, turbulence, mean-stress, and
    code-specific effects are not implemented.

## Development and verification constraints

-   Optional-backend tests require separate compatible environments. A base
    development environment legitimately skips those tests, while isolated CI
    jobs provide backend validation.
-   Chaospy and UQpy have constrained dependency/NumPy compatibility ranges;
    `docs/plugin_compatibility.md` is the source of truth.
-   On the current Windows sandbox, `conda activate offshoresafe-dev` may not
    modify the active shell. Verification should use the environment's Python
    executable or `conda run -n offshoresafe-dev <command>`.
-   The test cache may emit a permission warning when `.pytest_cache` is owned by
    another Windows identity. This does not change test outcomes, but the warning
    should not be mistaken for a product failure.

------------------------------------------------------------------------

# Next-Step Plan

## Completed Priority --- Issue #064 Engineering Analysis Workflow

The application-level path is now implemented:

    versioned OffshoreSafe project configuration
        -> solver adapter
        -> normalized SolverResult
        -> statistics / extremes / fatigue
        -> traceable serialized engineering result

The workflow is covered by OpenFAST and HEROWIND end-to-end tests and a fixed
OpenFAST benchmark. It is the reusable foundation for structural reliability
and reporting.

## Completed Priority --- Issue #070 Tower Reliability Vertical Slice

The first complete structural reliability application now:

-   define a tower limit-state contract in OffshoreSafe;
-   map normalized tower-load channels to the limit-state inputs;
-   describe material, geometry, and load uncertainty with UQRA objects;
-   run Monte Carlo and FORM through the existing UQRA API;
-   preserve the engineering-analysis provenance from Issue #064;
-   validate against a small analytical or published tower/beam reference case.

The implementation is covered by unit, configured OpenFAST workflow, native
FORM, native Monte Carlo, traceability, and analytical-reference benchmark
checks.

## Completed Priority --- Issue #071 Blade Fatigue Reliability

The second structural vertical slice now combines the rainflow/Miner pipeline
with uncertain load and S-N parameters, UQRA FORM/Monte Carlo, Issue #064
provenance, and an analytical-damage/fixed-FORM benchmark.

## Parallel Follow-up --- Harden Engineering Post-processing

Open focused follow-up issues only where application requirements justify them:

-   physical-time peak separation and event-rate estimation;
-   mean-stress and code-specific fatigue corrections;
-   uncertainty or goodness-of-fit diagnostics for extreme distributions;
-   additional solver adapters, prioritized by available verified fixtures.

These enhancements should not block the active metocean/floating-platform path
unless its acceptance fixtures demonstrate a concrete need.

## Priority 1 --- Issues #080 and #081 Metocean and Environmental Contour

Implement the domain-level wind, wave, and current probability model followed
by IFORM environmental contours. These become reusable inputs for the more
complex floating-platform workflow.

## Priority 2 --- Issue #072 Floating Platform Reliability

Proceed after the metocean and contour contracts stabilize:

1.  Floating-platform reliability, which depends on the broader metocean and
    solver-integration surface.
2.  Reporting and full traceability consolidation after the structural
    workflows produce stable result schemas.

------------------------------------------------------------------------

# Recommended Development Order

Completed foundation:

    UQRA core
        -> reliability algorithms
        -> benchmark suite
        -> plugin integration
        -> OffshoreSafe solver normalization
        -> engineering post-processing

Active critical path:

    Issues #080/#081 metocean and environmental contour
        -> Issue #072 floating-platform reliability
        -> Issues #090/#091 reporting and traceability

Core principle:

> Build a reliable uncertainty quantification and reliability framework
> first, then develop offshore engineering applications on top of it.
