"""Contract and native compatibility tests for Issue #040."""

from __future__ import annotations

import numpy as np
import pytest
from uqra import (
    FORM,
    Backend,
    BackendRegistry,
    Capability,
    NativeBackend,
    RandomVariable,
    RandomVector,
    ReliabilityProblem,
    ReliabilityResult,
    SamplingResult,
    SensitivityResult,
    available_backends,
    get_backend,
    normalize_reliability_result,
    normalize_sampling_result,
    normalize_sensitivity_result,
)


def rs_problem() -> ReliabilityProblem:
    variables = RandomVector(
        [
            RandomVariable("R", "Normal", {"mean": 100.0, "std": 10.0}),
            RandomVariable("S", "Normal", {"mean": 60.0, "std": 10.0}),
        ]
    )
    return ReliabilityProblem(variables, lambda x: x[0] - x[1])


def test_native_backend_is_discoverable_by_primary_name_and_alias() -> None:
    native = get_backend("native")

    assert native is get_backend("uqra")
    assert available_backends() == ("native",)
    assert native.supports(Capability.RELIABILITY_FORM)
    assert native.supports("sampling.sobol")
    assert not native.supports(Capability.SENSITIVITY_SOBOL)


def test_capability_detection_rejects_unknown_identifier() -> None:
    with pytest.raises(ValueError, match="unknown backend capability"):
        get_backend("native").supports("reliability.unknown")


def test_registry_rejects_duplicate_names_and_reports_missing_backend() -> None:
    registry = BackendRegistry()
    registry.register(NativeBackend(), aliases=("uqra",))

    with pytest.raises(ValueError, match="already registered"):
        registry.register(NativeBackend())
    with pytest.raises(ValueError, match="not available"):
        registry.get("missing")
    with pytest.raises(TypeError, match="Backend interface"):
        registry.register(object())  # type: ignore[arg-type]


def test_reliability_result_mapping_is_normalized() -> None:
    result = normalize_reliability_result(
        {
            "failure_probability": 0.01,
            "reliability_index": 2.326,
            "method": "external FORM",
            "metadata": {"backend": "example"},
        }
    )

    assert isinstance(result, ReliabilityResult)
    assert result.pf == pytest.approx(0.01)
    assert result.beta == pytest.approx(2.326)
    assert result.metadata["backend"] == "example"


def test_sampling_and_sensitivity_mappings_are_normalized() -> None:
    sampling = normalize_sampling_result(
        {"samples": [[0.1, 0.2]], "metadata": {"method": "external"}}
    )
    sensitivity = normalize_sensitivity_result(
        {"method": "Sobol", "indices": {"S1": [0.3, 0.7]}}
    )

    assert isinstance(sampling, SamplingResult)
    assert sampling.samples == pytest.approx(np.array([[0.1, 0.2]]))
    assert isinstance(sensitivity, SensitivityResult)
    assert sensitivity.indices["S1"] == [0.3, 0.7]


@pytest.mark.parametrize(
    "normalizer",
    [
        normalize_reliability_result,
        normalize_sampling_result,
        normalize_sensitivity_result,
    ],
)
def test_normalizers_reject_non_mapping_results(normalizer: object) -> None:
    with pytest.raises(TypeError, match="backend result must be a mapping"):
        normalizer(object())  # type: ignore[operator]


def test_native_reliability_backend_preserves_form_result() -> None:
    problem = rs_problem()
    direct = FORM(problem.variables, problem.limit_state).solve()
    dispatched = problem.solve("FORM", backend="native")
    aliased = problem.solve("FORM", backend="uqra")

    assert dispatched.beta == pytest.approx(direct.beta)
    assert dispatched.pf == pytest.approx(direct.pf)
    assert dispatched.metadata["backend"] == "native"
    assert aliased.beta == pytest.approx(direct.beta)


def test_native_sampling_backend_preserves_sampling_contract() -> None:
    backend = get_backend("native")
    result = backend.sample("LHS", 3, 16, random_state=42)  # type: ignore[attr-defined]

    assert isinstance(result, SamplingResult)
    assert result.samples.shape == (16, 3)
    assert np.all((result.samples >= 0.0) & (result.samples < 1.0))
    assert result.metadata["method"] == "latin_hypercube"
    assert result.metadata["backend"] == "native"


def test_backend_base_class_remains_abstract() -> None:
    with pytest.raises(TypeError):
        Backend()  # type: ignore[abstract]


def test_native_rejects_unknown_methods() -> None:
    backend = NativeBackend()
    with pytest.raises(ValueError, match="unsupported reliability"):
        backend.solve_reliability(rs_problem(), "unknown")
    with pytest.raises(ValueError, match="unsupported sampling"):
        backend.sample("unknown", 2, 4)
