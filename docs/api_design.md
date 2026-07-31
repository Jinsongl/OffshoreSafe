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
-   description

`name` and `distribution` must be non-empty strings. `parameters` is a
mapping copied into the object, so later changes to the input mapping do
not change the random-variable definition. Distribution-specific
operations are defined by the separate distribution interface.

------------------------------------------------------------------------

## Distribution Interface

All continuous distributions implement:

``` python
distribution.pdf(x)
distribution.cdf(x)
distribution.ppf(probability)
distribution.sample(size=1, random_state=None)
```

Initial implementations are `Normal(mean, std)`,
`Lognormal(mean, std)`, `Weibull(scale, shape)`, and
`Uniform(lower, upper)`. Lognormal `mean` and `std` are arithmetic-space
moments. `random_state` accepts an integer seed or a NumPy generator.

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
-   covariance input and correlation derivation;
-   copula;
-   transformation.

Variable names must be unique. A vector accepts either a correlation
matrix or a covariance matrix, validates that it is symmetric positive
semidefinite, and copies it into read-only storage. If neither is given,
the identity correlation matrix is used. `copula` and `transformation`
are backend extension points. `correlate()` maps independent
standard-normal samples to the configured Gaussian correlation.

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
