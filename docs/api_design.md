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

## Sampling Interface

Sampling engines generate points in the standard unit hypercube. Probability
distributions and transformations map these points to physical variables.

``` python
sampler = MonteCarloSampler(dimension=3)
result = sampler.sample(n_samples=1024, random_state=42)

result.samples   # shape: (1024, 3)
result.metadata  # method, n_samples, dimension, method-specific details
```

The common signature is `sample(n_samples, random_state=None) ->
SamplingResult`. `random_state` accepts an integer seed or a NumPy generator.
Initial engines are `MonteCarloSampler`, `LatinHypercubeSampler` (also exported
as `LHSSampler`), and `SobolSampler`. Sobol balance is guaranteed for
power-of-two sample counts and recorded in metadata. Samples and metadata are
read-only to preserve reproducibility.

------------------------------------------------------------------------

# 3. Limit State API

Definition:

    g(X)>0  safe

    g(X)<=0 failure

Examples:

    strength - stress

    capacity - damage

    allowable motion - response

Native API:

``` python
g = LimitStateFunction(lambda x: x[..., 0] - x[..., 1])
```

The constructor also accepts an external simulation model exposing
`evaluate(X)`. `evaluate_samples()` supports both vectorized analytical
functions and row-by-row external models. A scalar value greater than zero is
safe; zero and negative values are failure.

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

The implemented native solvers are selected through the same problem API:

``` python
mc_result = problem.solve("Monte Carlo", n_samples=100_000, random_state=42)
form_result = problem.solve("FORM")
sorm_result = problem.solve("SORM", correction="Breitung")
```

`ReliabilityResult` contains `pf` (and notation alias `Pf`), `beta`, `method`,
an optional confidence interval, physical and standard-normal design points,
sensitivity direction, convergence information, and method metadata. Monte
Carlo uses a Wilson confidence interval. FORM performs the Hasofer-Lind
minimum-distance design-point search in independent standard-normal space.
SORM supports the Breitung, Hohenbichler, and Tvedt corrections. Random-vector
correlation is represented with the existing Gaussian-copula transformation.

The built-in backend names are `"native"` and `"uqra"`. Other backend names
are resolved through the backend registry and fail explicitly until their
adapters are installed and registered. `ReliabilityBackend`, `SamplingBackend`,
and `SensitivityBackend` define the plugin contracts. Capability detection uses
stable `Capability` identifiers, while normalization helpers convert adapter
mappings into UQRA result objects.

OpenTURNS is an optional reliability backend:

``` python
problem.solve("FORM", backend="openturns")
problem.solve("SORM", backend="openturns", correction="Breitung")
```

Install it with `python -m pip install -e ".[openturns]"`. Importing UQRA does
not import OpenTURNS. The adapter supports Normal, arithmetic-moment Lognormal,
Weibull, and Uniform marginals plus Gaussian-copula correlation. Returned
metadata records `backend`, `backend_version`, `algorithm`, `correction`, and
`optimizer`.

UQpy is an optional sampling and reliability backend:

``` python
backend = get_backend("uqpy")
samples = backend.sample("LHS", dimension=3, n_samples=32, random_state=42)
form = problem.solve("FORM", backend="uqpy")
sorm = problem.solve("SORM", backend="uqpy")
```

Install it with `python -m pip install -e ".[uqpy]"`. The adapter converts
Normal, arithmetic-moment Lognormal, and Uniform marginals, passes Gaussian
correlation to UQpy FORM, and normalizes MC/LHS and FORM/SORM outputs. Metadata
records `backend`, `backend_version`, `algorithm`, and relevant method options.
UQpy remains absent from the core dependency graph and is imported only when
the backend executes.

The minimal surrogate backend API is:

``` python
backend = get_backend("chaospy")
result = backend.fit_surrogate(
    model,
    random_vector,
    "PCE",
    order=3,
    fit="quadrature",
)
predictions = result.predict(samples)
mean = result.statistics["mean"]
variance = result.statistics["variance"]
```

`SurrogateBackend.fit_surrogate()` is the plugin boundary. `SurrogateResult`
contains a callable predictor, summary statistics, and metadata. The optional
Chaospy adapter supports `fit="quadrature"` and `fit="regression"` for
independent Normal, Lognormal, Weibull, and Uniform variables. Install it with
`python -m pip install -e ".[chaospy]"`.

SALib uses the existing sensitivity contract:

``` python
backend = get_backend("salib")
sobol = backend.analyze_sensitivity(
    model,
    "Sobol",
    variables=random_vector,
    n_samples=4096,
    random_state=42,
)
morris = backend.analyze_sensitivity(
    model,
    "Morris",
    variables=random_vector,
    n_samples=64,
    random_state=42,
)
```

Sobol results expose `S1`, `S1_conf`, `ST`, `ST_conf`, and optional `S2` /
`S2_conf`. Morris results expose `mu`, `mu_star`, `sigma`, `mu_star_conf`, and
a descending variable `ranking`. Both are normalized as `SensitivityResult`.
Install the optional backend with `python -m pip install -e ".[salib]"`.

------------------------------------------------------------------------

# 5. OffshoreSafe API

Issue #050 establishes the application entry point:

``` python
from offshoresafe import OffshoreProject

project = OffshoreProject.load("project.yaml")
project.save("build/project.yaml")
```

`OffshoreProject` uses strict immutable schema components for project, turbine,
solver, and analysis information. Unknown fields, unsupported schema versions,
invalid IDs, duplicate analysis IDs, and missing referenced files are rejected.
Resolved file paths are absolute in memory and portable when serialized.

Issue #051 adds the solver integration contract:

``` python
from offshoresafe import SolverAdapter, SolverCapability, SolverResult

result = SolverResult(
    time=[0.0, 0.1],
    channels={"tower_base_moment": [100.0, 101.0]},
    units={"tower_base_moment": "kN m"},
    metadata={"adapter": "example"},
)
```

Concrete adapters implement `read_input()`, `read_output()`, and
`export_result()`; `map_channel()` provides canonical naming. `supports()`
performs capability detection. The normalized result validates time and channel
shape and does not expose mutable parser buffers.

OpenFAST ASCII results use the same contract:

``` python
from offshoresafe import OpenFASTAdapter

adapter = OpenFASTAdapter()
input_metadata = adapter.read_input("main.fst")
result = adapter.read_output("main.out")
adapter.export_result(result, "build/main.normalized.json")
```

The adapter records OpenFAST version, source paths and SHA-256 hashes, original
channel names, normalized units, and canonical channel names. It does not invoke
OpenFAST or introduce an OpenFAST dependency into UQRA.

`HEROWINDAdapter` applies the same normalized contract to HEROWIND YAML input
and comma-header text results. Shared HEROWIND/OpenFAST channel names therefore
produce identical canonical names for downstream post-processing.

Engineering channel statistics consume that common result contract:

``` python
from offshoresafe import compute_statistics

statistics = compute_statistics(result, ddof=0)
maximum = statistics["tower_base_fore_aft_moment"].maximum
rms = statistics["tower_base_fore_aft_moment"].rms
```

The immutable result exposes count, mean, standard deviation, minimum, maximum,
RMS, and unit for each selected channel while preserving source traceability.

Extreme-response processing uses the same normalized result:

``` python
peaks = extract_peaks(result, "tower_base_fore_aft_moment", threshold=1000.0)
fitted = fit_extreme_distribution(peaks, distribution="gumbel")
response_50_year = return_period_response(
    fitted, return_period=50.0, events_per_period=365.25
)
```

`extract_peaks()` supports maxima, minima, and absolute-magnitude peaks plus a
minimum sample separation. `fit_extreme_distribution()` supports Gumbel maxima
and positive two-parameter Weibull distributions. The return-period API uses
the non-exceedance probability `1 - 1 / (return_period * events_per_period)`.
Peak and fitted results are immutable and preserve units and source metadata.

Fatigue post-processing exposes ASTM E1049 rainflow cycles and explicit S-N /
Miner calculations:

``` python
cycles = count_rainflow(load_history)
curve = SNCurve(slope=3.0, log10_intercept=12.0)
damage = calculate_fatigue_damage(cycles, curve).damage
del_value = calculate_del(cycles, slope=3.0, equivalent_cycles=1.0e7)
```

Each rainflow cycle contains range, mean, and count (half or full cycle).
`SNCurve` uses `N = 10**log10_intercept / range**slope` and may define an
inclusive endurance limit. Miner damage sums `count / N`; DEL preserves the
same range-power damage over the requested equivalent cycle count.

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
