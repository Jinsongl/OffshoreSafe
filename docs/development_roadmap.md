# UQRA / OffshoreSafe Development Roadmap

## 1. Development Strategy

The project is divided into two products:

    UQRA
    General UQ and reliability framework

    OffshoreSafe
    Offshore engineering application platform

------------------------------------------------------------------------

# Phase 0: Foundation

Duration:

1 month

Goal:

Establish repository and development environment.

## Milestones

### M0.1 Repository

Progress:

-   [x] Python packaging and version management (Issue #002).
-   [x] Pytest and code-quality CI pipeline (Issue #003).

Tasks:

-   create package structure;
-   configure pyproject.toml;
-   setup pytest;
-   setup documentation.

Deliverables:

-   runnable Python package;
-   CI pipeline.

------------------------------------------------------------------------

### M0.2 Core Data Model

Progress:

-   [x] RandomVariable (Issue #010).
-   [x] Distribution interface (Issue #011).
-   [x] RandomVector (Issue #012).

Tasks:

Implement:

-   RandomVariable;
-   Distribution;
-   RandomVector;
-   Model;
-   Result objects.

benchmarks:

-   normal distribution;
-   lognormal distribution.

------------------------------------------------------------------------

# Phase 1: UQRA Core

Duration:

2-3 months

Goal:

Develop general UQ capability.

### Milestone 0.3 Sampling Engine

Progress:

-   [x] Monte Carlo sampling (Issue #020).
-   [x] Latin Hypercube sampling and Ishigami benchmark (Issue #021).
-   [x] Sobol low-discrepancy sampling (Issue #022).

Deliverables:

-   stable sampling result and sampler APIs;
-   reproducible unit-hypercube sampling;
-   unit tests, statistical validation, benchmark, and documentation.

------------------------------------------------------------------------

### Milestone 0.4 Reliability Engine

Progress:

-   [x] Limit-state function interface (Issue #030).
-   [x] Monte Carlo reliability (Issue #031).
-   [x] FORM and design-point search (Issue #032).
-   [x] SORM probability corrections (Issue #033).

Deliverables:

-   stable reliability result and solver APIs;
-   R-S, Four Branch, and nonlinear SORM benchmarks;
-   unit tests, numerical validation, benchmark, and documentation.

------------------------------------------------------------------------

## M1.1 Probability Module

Tasks:

-   probability distributions;
-   transformations;
-   correlation;
-   copula.

Acceptance:

Random variables can be created from YAML.

------------------------------------------------------------------------

## M1.2 Sampling Module

Tasks:

-   Monte Carlo;
-   Latin Hypercube;
-   Sobol sampling.

benchmarks:

-   Ishigami function.

------------------------------------------------------------------------

## M1.3 Reliability Module

Progress:

-   [x] LimitStateFunction (Issue #030).
-   [x] Monte Carlo reliability (Issue #031).
-   [x] FORM (Issue #032).
-   [x] SORM (Issue #033).

Tasks:

-   LimitStateFunction;
-   Monte Carlo reliability;
-   FORM;
-   SORM.

benchmarks:

-   R-S problem;
-   Four Branch Function.

------------------------------------------------------------------------

# Phase 2: UQRA Alpha Release

Duration:

1-2 months

Deliver:

-   stable API;
-   benchmarks suite;
-   documentation;
-   plugin interface.

Release acceptance:

-   [x] editable and isolated package installation;
-   [x] repeatable probability, sampling, and reliability benchmarks;
-   [x] stable public API and installation documentation;
-   [x] clean test and code-quality checks;
-   [x] `v0.1.0a1` release-candidate tag.

Version:

UQRA 0.1 Alpha

------------------------------------------------------------------------

## Milestone 1.1 Plugin Architecture

Progress:

-   [x] Backend interfaces, capability detection, and result normalization
    (Issue #040).
-   [x] Optional OpenTURNS distribution, FORM, and SORM adapter (Issue #041).
-   [x] Optional UQpy distribution, sampling, FORM, and SORM adapter (Issue #042).
-   [x] Minimal surrogate backend/result contract and optional Chaospy PCE adapter
    (Issue #043).
-   [x] Optional SALib Sobol and Morris sensitivity adapter (Issue #044).
-   [x] Plugin installation and compatibility matrix, isolated optional jobs,
    and Milestone 1.1 release review.

Deliverables:

-   `ReliabilityBackend`, `SamplingBackend`, and `SensitivityBackend`;
-   backend capability discovery;
-   normalized backend result contracts;
-   native-backend compatibility tests and documentation.
-   OpenTURNS conversion, reliability benchmarks, optional-dependency tests,
    and isolated CI validation.
-   UQpy conversion, Monte Carlo and Latin hypercube sampling, FORM/SORM result
    normalization, optional-dependency tests, benchmarks, and isolated CI validation.
-   `SurrogateBackend` and `SurrogateResult`, Chaospy distribution conversion,
    polynomial-chaos fitting/prediction/statistics, benchmarks, tests, documentation,
    and isolated CI validation.
-   SALib problem conversion, Sobol indices, Morris screening, normalized
    sensitivity results, Ishigami validation, ranking tests, documentation,
    benchmarks, and isolated CI validation.

------------------------------------------------------------------------

# Phase 3: OffshoreSafe MVP

Duration:

3-6 months

Goal:

Build offshore engineering workflow.

## M3.1 Solver Integration

Progress:

-   [x] Versioned `project.yaml` definition, strict validation, and path
    resolution (Issue #050).
-   [x] Unified `SolverAdapter` contract, normalized time-series result,
    channel mapping, export semantics, and compatibility benchmark (Issue #051).

Support:

-   HEROWIND;
-   OpenFAST;
-   Bladed;
-   OrcaFlex.

Functions:

-   result reading;
-   channel mapping;
-   unified data format.

------------------------------------------------------------------------

## M3.2 Engineering Post-processing

Functions:

-   statistics;
-   extreme response;
-   rainflow;
-   fatigue damage;
-   DEL.

------------------------------------------------------------------------

## M3.3 Structural Reliability

Applications:

-   tower reliability;
-   blade fatigue reliability;
-   floating platform reliability.

------------------------------------------------------------------------

# Phase 4: Engineering Application

Duration:

6-12 months

Goal:

Demonstrate engineering value.

Applications:

## Offshore Wind

-   IEC 61400-1 DLC reliability assessment;
-   IEC 61400-3 floating wind assessment;
-   fatigue reliability.

## Marine Structures

-   environmental contour;
-   extreme response;
-   structural safety.

------------------------------------------------------------------------

# Phase 5: Industrial Release

Long-term.

Functions:

-   advanced reliability;
-   Bayesian calibration;
-   surrogate acceleration;
-   HPC parallel analysis;
-   engineering reporting.

------------------------------------------------------------------------

# Recommended GitHub Milestones

    Milestone 0.1
    Foundation

    Milestone 0.2
    Probability Core

    Milestone 0.3
    Sampling

    Milestone 0.4
    Reliability Engine

    Milestone 1.0
    UQRA Alpha

    Milestone 2.0
    OffshoreSafe MVP

    Milestone 3.0
    Engineering Release

------------------------------------------------------------------------

# Development Principle

Priority order:

1.  Integrate existing mature algorithms.
2.  Build unified engineering workflow.
3.  Develop missing capabilities only when necessary.

Avoid rebuilding OpenTURNS.

Focus on:

    UQRA:
    Mathematical reliability engine

    OffshoreSafe:
    Engineering safety assessment workflow
