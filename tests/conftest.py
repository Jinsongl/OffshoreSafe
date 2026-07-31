"""Test configuration for source-layout packages."""

from __future__ import annotations

import sys
from pathlib import Path


UQRA_SOURCE = Path(__file__).parents[1] / "packages" / "uqra" / "src"
sys.path.insert(0, str(UQRA_SOURCE))
