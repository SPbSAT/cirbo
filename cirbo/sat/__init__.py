"""Subpackage contains methods related to SAT problem-solving including SAT solver
execution, reduction of Circuit SAT to SAT and building miter circuits, which are
helpful for circuit equivalence checking using."""

from .cnf import Cnf, tseytin_transformation
from .miter import build_miter
from .sat import (
    check_circuits_equivalence,
    is_circuit_satisfiable,
    is_satisfiable,
    PySatResult,
    PySATSolverNames,
)


__all__ = [
    # cnf.py
    'Cnf',
    'tseytin_transformation',
    # miter.py
    'build_miter',
    # sat.py
    'is_satisfiable',
    'is_circuit_satisfiable',
    'check_circuits_equivalence',
    'PySatResult',
    'PySATSolverNames',
]
