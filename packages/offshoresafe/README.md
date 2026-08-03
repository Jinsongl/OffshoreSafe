# OffshoreSafe

Offshore engineering workflow and probabilistic safety assessment application
layer built on UQRA.

Public application contracts currently include versioned project definitions
and the solver-independent `SolverAdapter` / `SolverResult` interface.
`EngineeringAnalysisWorkflow` connects those contracts to configured channel
statistics, extreme-response, and fatigue analyses and emits immutable,
traceable JSON-ready results.
