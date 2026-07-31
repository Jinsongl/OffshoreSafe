# UQRA / OffshoreSafe API Design

## 1. Architecture

    OffshoreSafe
        Engineering Application Layer

    UQRA
        General UQ and Reliability Framework

    Plugin Backends:
    OpenTURNS / FERUM / UQpy / Chaospy / SALib / PyMC

UQRA defines mathematical abstractions. OffshoreSafe defines engineering
workflows.

------------------------------------------------------------------------

# 2. UQRA Core API

## Random Variable

Example:

``` python
wind = RandomVariable(
    name="Vhub",
    distribution="Weibull",
    parameters={"scale":10.5, "shape":2.1}
)
```

Properties:

-   name
-   distribution
-   parameters
-   unit

------------------------------------------------------------------------

## Random Vector

``` python
vector = RandomVector(
    variables=[wind, wave_height],
    correlation_matrix=R
)
```

Supports:

-   correlation;
-   copula;
-   transformation.

------------------------------------------------------------------------

## Model Interface

All deterministic models implement:

``` python
evaluate(X)
```

Examples:

-   analytical models;
-   FEM models;
-   external simulation solvers.

------------------------------------------------------------------------

# 3. Limit State API

Definition:

    g(X)>0  safe

    g(X)<=0 failure

Examples:

    strength - stress

    capacity - damage

    allowable motion - response

------------------------------------------------------------------------

# 4. Reliability API

``` python
problem = ReliabilityProblem(
    variables=random_vector,
    limit_state=g
)

result = problem.solve(
    method="FORM",
    backend="OpenTURNS"
)
```

Methods:

-   Monte Carlo
-   FORM
-   SORM
-   Importance Sampling
-   Subset Simulation

Result:

-   failure probability Pf;
-   reliability index beta;
-   design point;
-   sensitivity.

------------------------------------------------------------------------

# 5. OffshoreSafe API

Example:

``` python
project = OffshoreProject("IEA15MW.yaml")

project.load_results(
    solver="OpenFAST"
)

project.extreme_analysis()

project.fatigue_analysis()

project.reliability()
```

Supported solvers:

-   HEROWIND
-   OpenFAST
-   Bladed
-   OrcaFlex

------------------------------------------------------------------------

# 6. API Rules

1.  Stable public API.
2.  No Offshore dependency inside UQRA.
3.  Backend switching shall not change user workflow.
4.  All results must contain traceability information.
