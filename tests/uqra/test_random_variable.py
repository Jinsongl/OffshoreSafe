"""Tests for the backend-independent RandomVariable model."""

from __future__ import annotations

import pytest
from uqra import RandomVariable, __version__


def test_package_exposes_development_version() -> None:
    assert __version__ == "0.1.0a2.dev0"


@pytest.mark.parametrize(
    ("distribution", "parameters"),
    [
        ("Normal", {"mean": 210e9, "std": 10e9}),
        ("Lognormal", {"mean": 100.0, "std": 10.0}),
        ("Weibull", {"scale": 10.5, "shape": 2.1}),
    ],
)
def test_supported_issue_010_distribution_metadata(
    distribution: str, parameters: dict[str, float]
) -> None:
    variable = RandomVariable(
        name="X",
        distribution=distribution,
        parameters=parameters,
        unit="Pa",
        description="Example uncertain quantity",
    )

    assert variable.name == "X"
    assert variable.distribution == distribution
    assert variable.parameters == parameters
    assert variable.unit == "Pa"
    assert variable.description == "Example uncertain quantity"


def test_parameters_are_copied_from_input_mapping() -> None:
    parameters = {"mean": 0.0, "std": 1.0}

    variable = RandomVariable("X", "Normal", parameters)
    parameters["mean"] = 5.0

    assert variable.parameters["mean"] == 0.0


@pytest.mark.parametrize("name", ["", "   ", None])
def test_name_must_be_a_non_empty_string(name: object) -> None:
    with pytest.raises(ValueError, match="name must be a non-empty string"):
        RandomVariable(name, "Normal", {})  # type: ignore[arg-type]


@pytest.mark.parametrize("distribution", ["", "   ", None])
def test_distribution_must_be_a_non_empty_string(distribution: object) -> None:
    with pytest.raises(ValueError, match="distribution must be a non-empty string"):
        RandomVariable("X", distribution, {})  # type: ignore[arg-type]


def test_parameters_must_be_a_mapping() -> None:
    with pytest.raises(TypeError, match="parameters must be a mapping"):
        RandomVariable("X", "Normal", [])  # type: ignore[arg-type]
