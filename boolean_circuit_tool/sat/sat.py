import pysat

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.cnf import Cnf


__all__ = ['is_satisfiable']


def is_satisfiable(circuit: Circuit) -> bool:
    g = pysat.formula.CNF()
    for clause in Cnf.from_circuit(circuit).get_raw():
        g.append(g)
    with pysat.solvers.Lingeling(bootstrap_with=g.clauses, with_proof=True) as l:
        return l.solve()


def check():
    for size in range(3, 16):

