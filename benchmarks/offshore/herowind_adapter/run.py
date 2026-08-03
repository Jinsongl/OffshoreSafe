"""Deterministic Issue #053 HEROWIND adapter benchmark."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[3]
sys.path[:0] = [
    str(ROOT / "packages" / "offshoresafe" / "src"),
    str(ROOT / "packages" / "uqra" / "src"),
]

from offshoresafe import HEROWINDAdapter  # noqa: E402


def main() -> None:
    case = Path(__file__).parent
    expected = yaml.safe_load(
        (case / "expected_result.yaml").read_text(encoding="utf-8")
    )
    adapter = HEROWINDAdapter()
    result = adapter.read_output(case / "output" / "MultibodyOutput.txt")
    assert result.sample_count == expected["sample_count"]
    assert list(result.channel_names) == expected["channels"]
    assert (
        result.channels["tower_base_fore_aft_moment"][-1]
        == expected["final_tower_base_fore_aft_moment"]
    )
    print(f"HEROWIND adapter benchmark passed: {result.sample_count} samples")


if __name__ == "__main__":
    main()
