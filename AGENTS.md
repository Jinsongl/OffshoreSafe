# AGENTS.md

## Project Identity

This repository contains:

    UQRA

    General Uncertainty Quantification and Reliability Analysis Framework


    OffshoreSafe

    Probabilistic Design and Assessment Platform for Offshore Energy Systems

------------------------------------------------------------------------

# Core Principle

    UQRA = Mathematical and algorithmic foundation

    OffshoreSafe = Engineering application layer

Never mix these responsibilities.

------------------------------------------------------------------------

# UQRA Rules

UQRA shall:

-   remain domain independent;
-   provide probability and reliability algorithms;
-   support plugin backends.

UQRA shall not contain:

-   wind turbine models;
-   offshore structures;
-   IEC assumptions;
-   marine engineering logic.

------------------------------------------------------------------------

# OffshoreSafe Rules

OffshoreSafe shall:

-   use UQRA;
-   manage offshore engineering workflows;
-   connect simulation results;
-   perform safety assessment.

------------------------------------------------------------------------

# Dependency Rules

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

------------------------------------------------------------------------

# Plugin Rules

External software should be integrated as optional backends:

-   OpenTURNS
-   FERUM
-   UQpy
-   Chaospy
-   SALib
-   PyMC
-   emcee
-   Tasmanian

Do not tightly couple the core to one package.

------------------------------------------------------------------------

# Development Rules

Before coding:

1.  Read specs.md.
2.  Read architecture.md.
3.  Check benchmark_plan.md.
4.  Update roadmap.

Every algorithm requires:

-   API definition;
-   tests;
-   benchmark;
-   documentation.



------------------------------------------------------------------------

## Development Environment

Python environment:

conda env:
offshoresafe-dev

Python version:
3.11

Before running Python commands:

conda activate offshoresafe-dev

------------------------------------------------------------------------

# Long Term Vision

Build:

    UQRA
    Python reliability framework

    +

    OffshoreSafe
    Offshore engineering safety assessment platform

The goal is integration and engineering workflow, not simply rebuilding
existing libraries.



