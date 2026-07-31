# Coding Standard

## 1. General

Language:

-   Python \>= 3.11

Follow:

-   PEP8;
-   type hints;
-   modular design;
-   clear documentation.

------------------------------------------------------------------------

# 2. Package Structure

    src/

    tests/

    examples/

    benchmarks/

    docs/

------------------------------------------------------------------------

# 3. Testing Requirement

Every feature requires:

1.  Unit test.
2.  Example.
3.  Documentation.

Numerical algorithms require benchmark validation.

Example:

    reliability/

    tests/
        test_form.py

    benchmarks/
        rs_problem/

------------------------------------------------------------------------

# 4. Benchmark Rule

Each algorithm requires:

-   reference case;
-   expected result;
-   tolerance;
-   comparison source.

Sources:

-   OpenTURNS;
-   FERUM;
-   published literature.

------------------------------------------------------------------------

# 5. Git Convention

Format:

    type(module): description

Examples:

    feat(uqra): add FORM solver

    fix(reliability): correct beta calculation

    test(benchmark): add beam case

    docs(api): update interface

------------------------------------------------------------------------

# 6. Review Rule

Before merge:

-   tests pass;
-   benchmark passes;
-   documentation updated;
-   no unnecessary dependency added.

------------------------------------------------------------------------

# 7. Architecture Rule

Allowed:

    OffshoreSafe -> UQRA

Forbidden:

    UQRA -> OffshoreSafe

UQRA remains domain independent.
