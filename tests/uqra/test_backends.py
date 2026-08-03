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
    SurrogateResult,
    available_backends,
    get_backend,
    normalize_reliability_result,
    normalize_sampling_result,
    normalize_sensitivity_result,
    normalize_surrogate_result,
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
    assert available_backends() == (
        "chaospy",
        "native",
        "openturns",
        "salib",
        "uqpy",
    )
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


def test_surrogate_mapping_is_normalized_and_predictable() -> None:
    result = normalize_surrogate_result(
        {
            "method": "external PCE",
            "predictor": lambda samples: np.asarray(samples)[:, 0],
            "statistics": {"mean": 0.5},
            "metadata": {"backend": "example"},
        }
    )

    assert isinstance(result, SurrogateResult)
    assert result.predict([[0.25], [0.75]]) == pytest.approx([0.25, 0.75])
    assert result.statistics["mean"] == pytest.approx(0.5)


@pytest.mark.parametrize(
    "normalizer",
    [
        normalize_reliability_result,
        normalize_sampling_result,
        normalize_sensitivity_result,
        normalize_surrogate_result,
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


def test_importing_uqra_does_not_import_optional_backends() -> None:
    import os
    import subprocess
    import sys
    from pathlib import Path

    import uqra

    source_root = Path(uqra.__file__).parents[1]
    environment = {**os.environ, "PYTHONPATH": str(source_root)}
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, uqra; "
            "assert 'openturns' not in sys.modules; "
            "assert 'UQpy' not in sys.modules; "
            "assert 'chaospy' not in sys.modules; "
            "assert 'SALib' not in sys.modules",
        ],
        cwd=source_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr


def test_openturns_missing_dependency_has_actionable_error(monkeypatch: object) -> None:
    import uqra.backends.openturns as adapter

    def missing(name: str) -> None:
        raise ModuleNotFoundError(name="openturns")

    monkeypatch.setattr(adapter, "import_module", missing)  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match=r"\[openturns\]"):
        adapter.OpenTURNSBackend().solve_reliability(rs_problem(), "FORM")


def test_uqpy_missing_dependency_has_actionable_error(monkeypatch: object) -> None:
    import uqra.backends.uqpy as adapter

    def missing(name: str) -> None:
        raise ModuleNotFoundError(name="UQpy")

    monkeypatch.setattr(adapter, "import_module", missing)  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match=r"\[uqpy\]"):
        adapter.UQpyBackend().sample("MC", 2, 4)


def test_chaospy_missing_dependency_has_actionable_error(monkeypatch: object) -> None:
    import uqra.backends.chaospy as adapter

    def missing(name: str) -> None:
        raise ModuleNotFoundError(name="chaospy")

    monkeypatch.setattr(adapter, "import_module", missing)  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match=r"\[chaospy\]"):
        adapter.ChaospyBackend().fit_surrogate(lambda x: x[0], object())


def test_salib_missing_dependency_has_actionable_error(monkeypatch: object) -> None:
    import uqra.backends.salib as adapter

    def missing(name: str) -> None:
        raise ModuleNotFoundError(name="SALib")

    monkeypatch.setattr(adapter, "import_module", missing)  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match=r"\[salib\]"):
        adapter.SALibBackend().analyze_sensitivity(lambda x: x[0], "Sobol")
