# Metocean Models and IFORM Environmental Contours

Issues #080 and #081 provide correlated offshore environmental variables and a
domain-independent inverse FORM contour algorithm.

## Architecture

-   UQRA owns the IFORM reliability radius, standard-normal directions, Gaussian
    transformation, and physical contour points.
-   OffshoreSafe owns metocean variable names, units, marginal definitions,
    engineering configuration, and named environmental results.

The dependency remains `OffshoreSafe -> UQRA`.

## Probability model

`MetoceanModel` accepts two or more named variables from significant wave
height, peak period, wind speed/current speed, and wind/wave/current direction.
Native Normal, Lognormal, Weibull, and Uniform marginals are available through
UQRA. Dependence currently uses a Gaussian copula correlation matrix.

## IFORM definition

For return period `T` and `n` independent events per period:

``` text
p = 1 / (T * n)
beta = Phi^-1(1 - p)
```

Two-dimensional contours use evenly spaced directions on the standard-normal
circle of radius `beta`. Higher-dimensional surfaces require explicit non-zero
directions; the implementation normalizes them before applying the radius.

## Example

``` python
from offshoresafe import MetoceanModel

model = MetoceanModel.from_config({
    "variables": {
        "significant_wave_height": {
            "distribution": "Weibull",
            "parameters": {"scale": 3.0, "shape": 2.0},
            "unit": "m",
        },
        "peak_period": {
            "distribution": "Lognormal",
            "parameters": {"mean": 9.0, "std": 1.2},
            "unit": "s",
        },
    },
    "correlation_matrix": [[1.0, 0.35], [0.35, 1.0]],
})
contour = model.iform_contour(50.0, events_per_period=365.25, n_points=72)
```

## Scope and limitations

-   Correlation is Gaussian-copula dependence, not a conditional Hs–Tp model or
    arbitrary vine copula.
-   Event independence and the correct event rate are caller assumptions.
-   The contour is an environmental probability surface; it is not a response-
    based contour and does not by itself establish structural reliability.
-   Directional wrapping, seasonality, climate non-stationarity, tides, and
    site-specific hindcast fitting are not implicit.
-   The Hs–Tp fixture is software verification, not a site assessment.

## Verification

``` powershell
python -m pytest -q tests/uqra/test_iform.py tests/offshoresafe/test_metocean.py
python benchmarks/offshore/environmental_contour/run.py
```
