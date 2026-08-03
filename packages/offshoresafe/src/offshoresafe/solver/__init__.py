"""External solver integration contracts."""

from offshoresafe.solver.base import SolverAdapter, SolverCapability
from offshoresafe.solver.herowind import HEROWINDAdapter
from offshoresafe.solver.openfast import OpenFASTAdapter
from offshoresafe.solver.result import SolverResult

__all__ = [
    "HEROWINDAdapter",
    "OpenFASTAdapter",
    "SolverAdapter",
    "SolverCapability",
    "SolverResult",
]
