from typing import Tuple, Any

import pysat
import typing as tp

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.cnf import Cnf
from boolean_circuit_tool.synthesis.circuit_search import PySATSolverNames


__all__ = ['is_satisfiable']


def is_satisfiable(circuit: Circuit, solver_name: tp.Union[PySATSolverNames, str] = PySATSolverNames.CADICAL193,) -> (bool, list[int]):
    g = pysat.solvers.Glucose3()
    for clause in Cnf.from_circuit(circuit).get_raw():
        g.add_clause(g)
    return g.solve(), g.get_model()


def check():
    for size in range(3, 16):
        pass

