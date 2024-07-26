import typing as tp

from boolean_circuit_tool.cnf.tseytin import Tseytin
from boolean_circuit_tool.cnf.utils import Clause, CnfRaw

from boolean_circuit_tool.core.circuit import Circuit


__all__ = ['Cnf']


class Cnf:
    """Class for CNF storage."""

    def __init__(self, cnf: tp.Optional[CnfRaw] = None):
        """

        :param cnf: CNF can be not assigned, it means cnf is empty.
        """
        if cnf is None:
            self._cnf = []
        else:
            self._cnf = cnf

    @staticmethod
    def from_circuit_tseytin(circuit: Circuit) -> 'Cnf':
        """
        Converts circuit to CNF by Tseytin transformation and returns CNF.

        :param circuit: Circuit what will be converted to cnf.

        """
        return Cnf(Tseytin(circuit).to_cnf())

    def add_clause(self, clause: Clause):
        """
        Add clause to CNF.

        :param clause: new clause.

        """
        self._cnf.append(clause)

    def get_raw(self) -> CnfRaw:
        """Returns CnfRaw object."""
        return self._cnf
