# OffshoreSafe / UQRA Architecture Design

## 1. Architecture Objective

The software ecosystem adopts a layered architecture:

                        OffshoreSafe
            Offshore Energy Engineering Application Layer

                             |
                             |

                           UQRA
          General Uncertainty Quantification and Reliability Engine

                             |
                             |

                  Algorithm Backend Layer

     OpenTURNS | FERUM | UQpy | Chaospy | SALib | PyMC | emcee | Tasmanian

The core principle:

> UQRA provides mathematical algorithms. OffshoreSafe provides
> engineering workflows and domain knowledge.

------------------------------------------------------------------------

# 2. Design Principles

## 2.1 Separation of Concerns

UQRA shall not depend on OffshoreSafe.

Allowed:

    OffshoreSafe
          |
          v
        UQRA

Forbidden:

    UQRA
          |
          v
    OffshoreSafe

Reason:

-   UQRA remains a reusable open-source framework.
-   OffshoreSafe becomes one engineering application.
-   Other industries can reuse UQRA.

------------------------------------------------------------------------

## 2.2 Backend Independence

Algorithms should not be tightly coupled to a specific package.

Example:

User:

``` python
result = reliability.solve(method="FORM")
```

Internal selection:

    FORM
     |
     +-- UQRA native implementation
     |
     +-- OpenTURNS backend
     |
     +-- other backend

------------------------------------------------------------------------

# 3. UQRA Core Architecture

## 3.1 Package Structure

    uqra/

    core/
        problem.py
        variable.py
        distribution.py
        random_vector.py
        model.py

    sampling/
        monte_carlo.py
        lhs.py
        sobol.py
        importance_sampling.py

    reliability/
        limit_state.py
        form.py
        sorm.py
        monte_carlo.py
        reliability_result.py

    surrogate/
        pce.py
        kriging.py
        gaussian_process.py

    sensitivity/
        sobol.py
        morris.py

    bayesian/
        mcmc.py
        calibration.py

    plugins/
        openturns_backend.py
        uqpy_backend.py
        chaospy_backend.py
        salib_backend.py
        pymc_backend.py
        emcee_backend.py
        tasmanian_backend.py

    io/
        yaml.py
        json.py
        result.py

------------------------------------------------------------------------

# 4. UQRA Core Object Model

## 4.1 Random Variable

Represents uncertain parameters.

Example:

    Wind speed
    Material strength
    Thickness
    Damping coefficient

Object:

    RandomVariable

    name
    distribution
    parameters
    unit

------------------------------------------------------------------------

## 4.2 Random Vector

Combines correlated variables.

Example:

    X = [Hs, Tp, WindSpeed]

Object:

    RandomVector

    variables
    correlation
    copula
    transformation

------------------------------------------------------------------------

## 4.3 Model

Represents deterministic or simulation model.

Examples:

    Analytical function

    Finite element model

    HEROWIND simulation

    OpenFAST simulation

Object:

    Model

    input
    output
    evaluate()

------------------------------------------------------------------------

## 4.4 Limit State Function

Core reliability object.

Definition:

    g(X) > 0 : safe

    g(X) <= 0 : failure

Examples:

    Strength - Load

    Allowable stress - Stress

    Fatigue capacity - Damage

Object:

    LimitStateFunction

    variables
    model
    failure_condition

------------------------------------------------------------------------

## 4.5 Reliability Problem

Combines uncertainty and failure definition.

Object:

    ReliabilityProblem

    random_variables
    limit_state
    method
    result

Output:

    Pf

    Beta

    Design Point

    Sensitivity

------------------------------------------------------------------------

# 5. OffshoreSafe Architecture

## 5.1 Package Structure

    offshoresafe/

    project/
        project_definition
        design_basis

    metocean/
        wind
        wave
        current
        environmental_contour

    cases/
        dlc
        load_case
        simulation_case

    solver/
        base_adapter
        herowind
        openfast
        bladed
        orcaflex

    postprocessing/
        channel_mapping
        statistics
        extreme
        fatigue
        rainflow

    structural/
        blade
        tower
        foundation
        floating_platform
        mooring

    assessment/
        ultimate_limit_state
        fatigue_reliability
        safety_margin

    report/
        excel
        pdf
        traceability

------------------------------------------------------------------------

# 6. Solver Adapter Architecture

All simulation programs shall follow the same interface.

    SolverAdapter

        read_input()

        read_output()

        map_channel()

        export_result()

Supported:

    HEROWIND

    OpenFAST

    Bladed

    OrcaFlex

Generic CSV

The Issue #051 contract normalizes solver output as an immutable
`SolverResult` containing time, canonical channels, units, and metadata.
Capability detection is available without loading a solver SDK. Execution is a
separate orchestration concern and may be added by concrete integrations.

`OpenFASTAdapter` is the first concrete implementation. It reads primary input
metadata and ASCII output tables directly, maps common load and motion channels,
and attaches file hashes and solver version to the normalized result. Binary
output and solver execution remain outside this adapter boundary.

------------------------------------------------------------------------

## 6.1 Project Definition Boundary

OffshoreSafe is packaged separately under `packages/offshoresafe` and declares
UQRA as a dependency. Its versioned `project.yaml` models project, turbine,
solver, and analysis configuration. Paths are resolved by the application layer
before later solver adapters execute. UQRA contains no project-schema or
offshore-domain imports.

------------------------------------------------------------------------

# 7. Data Flow

Complete workflow:

    Project Definition

            |

    Uncertainty Model

            |

    Sampling

            |

    Simulation Cases

            |

    External Solver

            |

    Time Series Results

            |

    Post Processing

            |

    Limit State

            |

    Reliability Analysis

            |

    Engineering Report

------------------------------------------------------------------------

# 8. Traceability Architecture

Every result must contain:

    Project ID

    Case ID

    Sample ID

    Solver Version

    Input File Hash

    Output File Hash

    Processing Method

    Software Version

    Timestamp

Purpose:

-   reproducibility;
-   engineering review;
-   certification support.

------------------------------------------------------------------------

# 9. Recommended Development Order

Phase 1:

    UQRA core objects
    +
    sampling
    +
    basic reliability

Phase 2:

    OffshoreSafe workflow
    +
    solver adapters
    +
    post-processing

Phase 3:

    Advanced reliability
    +
    environmental contour
    +
    engineering reports
