# OffshoreSafe / UQRA benchmarks Plan

## 1. Purpose

The benchmarks system validates:

1.  UQRA mathematical reliability capability.
2.  Compatibility with existing tools.
3.  OffshoreSafe engineering workflow.
4.  Accuracy and reproducibility.

Reference software:

-   OpenTURNS
-   FERUM
-   UQpy
-   UQLab
-   Dakota

------------------------------------------------------------------------

# 2. benchmarks Levels

    Level 0
    Mathematical Reliability

            |

    Level 1
    Structural Reliability

            |

    Level 2
    Offshore Engineering Reliability

------------------------------------------------------------------------

# 3. Level 0: Mathematical Reliability Benchmarks

## Core Probability Data Model

Purpose:

-   validate analytical Normal, Lognormal, Weibull, and Uniform values;
-   validate distribution sampling moments;
-   recover a configured Gaussian correlation matrix from transformed
    standard-normal samples.

Reference:

-   analytical probability formulas;
-   SciPy distribution definitions.

Tolerance:

-   analytical values: numerical approximation tolerance;
-   sampled moments: 1 percent;
-   Gaussian correlation: absolute tolerance 0.01.

------------------------------------------------------------------------

## Case 1: R-S Problem

## Purpose

Basic reliability verification.

## Random Variables

    Resistance R

    Load S

## Limit State

    g(X)=R-S

## Evaluation

Compare:

-   FORM
-   SORM
-   Monte Carlo

## Reference

-   FERUM
-   OpenTURNS

------------------------------------------------------------------------

# Case 2: Four Branch Function

## Purpose

Nonlinear reliability benchmarks.

Characteristics:

-   multiple failure regions;
-   nonlinear limit state.

Evaluate:

-   FORM accuracy;
-   importance sampling;
-   subset simulation.

------------------------------------------------------------------------

# Case 3: Ishigami Function

## Purpose

Global sensitivity benchmarks.

Evaluate:

-   Sobol indices;
-   variance decomposition.

Reference:

SALib.

Sampling baseline:

-   map unit-cube samples to `[-pi, pi]^3`;
-   compare Monte Carlo and Latin Hypercube estimates with the analytical
    mean `a / 2 = 3.5`;
-   use a fixed seed for reproducibility.

------------------------------------------------------------------------

## Optional OpenTURNS Backend Compatibility

Purpose:

-   validate UQRA-to-OpenTURNS distribution and correlation conversion;
-   compare R-S and Four Branch FORM with analytical and native results;
-   verify linear SORM reduction and nonlinear Breitung, Hohenbichler, and
    Tvedt probability order of magnitude;
-   keep the optional backend outside native test and dependency paths.

Run:

    python benchmarks/mathematical/openturns_backend/run.py

------------------------------------------------------------------------

# 4. Level 1: Structural Reliability Benchmarks

## Case 4: Axial Beam

## Model

Axially loaded beam.

Random variables:

    Elastic modulus

    Cross-section

    Load

    Geometry

Failure:

    Stress > Allowable stress

Outputs:

    Failure probability

    Reliability index

Reference:

OpenTURNS.

------------------------------------------------------------------------

# Case 5: Cantilever Beam

## Model

Cantilever beam under transverse load.

Random variables:

    Elastic modulus

    Moment of inertia

    Load

    Length

Response:

    Tip displacement

Failure:

    u > u_limit

Purpose:

Validate structural response reliability.

------------------------------------------------------------------------

# Case 6: 25-Bar Truss

## Model

Classical truss reliability problem.

Random variables:

    Material properties

    Member areas

    Loads

Responses:

    Stress

    Displacement

Reference:

FERUM.

------------------------------------------------------------------------

# Case 7: Buckling Reliability

## Model

Column stability problem.

Random variables:

    Elastic modulus

    Geometry

    Initial imperfection

    Load

Failure:

    Critical load exceeded

Purpose:

Reference for offshore tower stability.

------------------------------------------------------------------------

# 5. Level 2: OffshoreSafe Engineering Benchmarks

## Case 8: Wind Turbine Tower Reliability

## Input

From:

-   HEROWIND
-   OpenFAST
-   Bladed

Uncertainties:

    Wind condition

    Material properties

    Thickness

    Damping

    Load uncertainty

Response:

    Tower base bending moment

Limit State:

    Resistance - Load

Outputs:

    Pf

    Beta

    Sensitivity

------------------------------------------------------------------------

# Case 9: Blade Fatigue Reliability

## Input

Simulation:

    Wind turbine aeroelastic simulation

Uncertainties:

    Wind speed

    Turbulence

    Blade stiffness

    S-N curve parameters

Response:

    Blade root moment

Assessment:

    Rainflow

    Miner damage

    Fatigue reliability

------------------------------------------------------------------------

# Case 10: Floating Platform Reliability

## Input

Environmental variables:

    Hs

    Tp

    Wave direction

    Current

    Wind

Responses:

    Platform motion

    Mooring tension

Assessment:

    Extreme response

    Mooring reliability

    Motion limit state

------------------------------------------------------------------------

# 6. Accuracy Evaluation Criteria

## Algorithm Level

Compare:

    Pf

    Beta

    Design point

    Sensitivity

against reference software.

------------------------------------------------------------------------

## Engineering Level

Compare:

    Response distribution

    Extreme value

    Fatigue damage

    Reliability index

against:

-   OpenFAST;
-   Bladed;
-   reference solutions.

------------------------------------------------------------------------

# 7. Continuous benchmarks Framework

Recommended structure:

    benchmarks/

    mathematical/
        rs_problem
        four_branch
        ishigami

    structural/
        axial_beam
        cantilever_beam
        truss25

    offshore/
        tower
        blade
        floating_platform

Each benchmarks contains:

    input.yaml

    model.py

    run.py

    expected_result.yaml

    README.md

Optional backend compatibility suites are kept in separate directories and CI
jobs. `mathematical/openturns_backend` validates Issue #041;
`mathematical/uqpy_backend` validates Issue #042 using the analytical R-S
problem, correlated Gaussian FORM, linear SORM degeneration, and reproducible
Latin hypercube strata.
`mathematical/chaospy_backend` validates Issue #043 using exact quadratic PCE
recovery through both quadrature and regression, plus Ishigami mean and
variance against analytical values.
`mathematical/salib_backend` validates Issue #044 using analytical Ishigami
Sobol indices and fixed-seed Morris ranking/reproducibility.

`offshore/solver_adapter_interface` validates the Issue #051 normalized
time-series contract independently of any external engineering solver. Concrete
solver formats are covered by their own adapter benchmarks in subsequent issues.
`offshore/openfast_adapter` validates Issue #052 with a deterministic primary
input and ASCII output fixture, known channel mapping, units, metadata, and
tower-base moment.
`offshore/herowind_adapter` validates Issue #053 against the verified HEROWIND
comma-header/whitespace-data convention, including units and unified channels.
`offshore/statistics` validates Issue #060 mean, population standard deviation,
minimum, maximum, and RMS against a five-point analytical sequence.
`offshore/extreme_response` validates Issue #061 peak extraction and a Gumbel
return-level calculation against SciPy's analytical quantile evaluation.
`offshore/fatigue` validates Issues #062 and #063 using a constant-amplitude
history with analytical rainflow count, Miner damage, and DEL.

------------------------------------------------------------------------

# 8. benchmarks Development Priority

## First 3 Months

Required:

1.  R-S problem.
2.  Four branch.
3.  Axial beam.
4.  Cantilever beam.

## 3-6 Months

Add:

5.  25-Bar truss.
6.  Buckling.
7.  Tower reliability.

## 6-12 Months

Add:

8.  Blade fatigue.
9.  Floating platform reliability.
10. Environmental contour.
