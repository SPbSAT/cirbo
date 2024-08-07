import dataclasses
import enum
import typing as tp

from pysat.formula import CNF
from pysat.solvers import Solver

from boolean_circuit_tool.cnf import Cnf

from boolean_circuit_tool.core.circuit import Circuit


__all__ = ['is_satisfiable', 'PySatResult', 'PySATSolverNames']


class PySATSolverNames(enum.Enum):
    """Enum version of pysat.solvers.SolverNames."""

    CADICAL103 = 'cadical103'
    CADICAL153 = 'cadical153'
    CADICAL193 = 'cadical195'
    CRYPTOSAT = 'crypto'
    GLUECARD3 = 'gluecard3'
    GLUECARD4 = 'gluecard4'
    GLUCOSE3 = 'glucose3'
    GLUCOSE4 = 'glucose4'
    GLUCOSE42 = 'glucose42'
    LINGELING = 'lingeling'
    MAPLECHRONO = 'maplechrono'
    MAPLECM = 'maplecm'
    MAPLESAT = 'maplesat'
    MERGESAT3 = 'mergesat3'
    MINICARD = 'minicard'
    MINISAT22 = 'minisat22'
    MINISATGH = 'minisat-gh'


@dataclasses.dataclass(frozen=True)
class PySatResult:
    """
    Class for is_satisfiable result.

    answer is bool, model shows var values, like [1, -2, 3, -4, ...].
    Model is None if answer is False.

    """

    answer: bool
    model: tp.Optional[list[int]]


def is_satisfiable(
    circuit: Circuit,
    *,
    solver_name: tp.Union[PySATSolverNames, str] = PySATSolverNames.CADICAL193,
) -> PySatResult:
    """
    Check if circuit is satisfiable using specific solver.

    @param circuit: circuit. @param solver_name: solver type/name, be default,
    cadical103.

    """
    formula = CNF(from_clauses=Cnf.from_circuit(circuit).get_raw())
    if isinstance(solver_name, PySATSolverNames):
        solver_name = solver_name.value
    with Solver(name=solver_name) as solver:
        solver.append_formula(formula)
        return PySatResult(solver.solve(), solver.get_model())
