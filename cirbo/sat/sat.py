import dataclasses
import enum
import typing as tp

import pysat.formula
import pysat.solvers

from cirbo.core.circuit import Circuit
from cirbo.sat.cnf import Cnf


__all__ = [
    'is_satisfiable',
    'is_circuit_satisfiable',
    'PySatResult',
    'PySATSolverNames',
]


class PySATSolverNames(enum.Enum):
    """Enum version of pysat.solvers.SolverNames."""

    CADICAL103 = 'cadical103'
    CADICAL153 = 'cadical153'
    CADICAL195 = 'cadical195'
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
    cnf: Cnf,
    *,
    solver_name: tp.Union[PySATSolverNames, str] = PySATSolverNames.CADICAL195,
) -> PySatResult:
    """
    Checks if provided ``Cnf`` is satisfiable using specified solver.

    :param cnf: Cnf formula to be checked for satisfiability.
    :param solver_name: solver type/name.
    :return: result returned from PySat.

    """
    solver_name = PySATSolverNames(solver_name)
    _pysat_cnf = pysat.formula.CNF(from_clauses=cnf.get_raw())
    with pysat.solvers.Solver(name=solver_name.value) as _solver:
        _solver.append_formula(_pysat_cnf)
        return PySatResult(_solver.solve(), _solver.get_model())


def is_circuit_satisfiable(
    circuit: Circuit,
    *,
    solver_name: tp.Union[PySATSolverNames, str] = PySATSolverNames.CADICAL195,
) -> PySatResult:
    """
    Checks if circuit is satisfiable using specified solver. Uses Tseytin transformation
    to construct SAT instance based on the provided ``Circuit`` (Circuit SAT) instance.

    :param circuit: Circuit representing a Circuit SAT instance.
    :param solver_name: solver type/name.
    :return: result returned from PySat.

    """
    return is_satisfiable(
        cnf=Cnf.from_circuit(circuit),
        solver_name=solver_name,
    )
