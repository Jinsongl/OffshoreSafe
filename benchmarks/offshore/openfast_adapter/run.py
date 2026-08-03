"""Deterministic Issue #052 OpenFAST adapter benchmark."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT / "packages" / "offshoresafe" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "uqra" / "src"))

from offshoresafe import OpenFASTAdapter  # noqa: E402


def main() -> None:
    case = Path(__file__).parent
    expected = yaml.safe_load(
        (case / "expected_result.yaml").read_text(encoding="utf-8")
    )
    adapter = OpenFASTAdapter()
    input_data = adapter.read_input(case / "input" / "main.fst")
    result = adapter.read_output(case / "output" / "main.out")

    assert input_data["solver_version"] == expected["solver_version"]
    assert result.metadata["solver_version"] == expected["solver_version"]
    assert result.sample_count == expected["sample_count"]
    assert list(result.channel_names) == expected["channels"]
    assert (
        result.channels["tower_base_fore_aft_moment"][-1]
        == expected["final_tower_base_fore_aft_moment"]
    )
    print(
        "OpenFAST adapter benchmark passed: "
        f"v{input_data['solver_version']}, {result.sample_count} samples"
    )


if __name__ == "__main__":
    main()
