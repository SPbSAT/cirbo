import typing as tp

from boolean_circuit_tool.core.circuit import Circuit


__all__ = ['Cnf', 'Lit', 'Clause', 'CnfRaw']


Lit = int
Clause = list[Lit]
CnfRaw = list[Clause]


class Cnf:
    """Structure to store CNF formula."""

    @staticmethod
    def from_circuit(circuit: Circuit) -> 'Cnf':
        """
        Converts circuit to CNF by Tseytin transformation and returns CNF.

        :param circuit: Circuit what will be converted to cnf.

        """
        from boolean_circuit_tool.sat.cnf.tseytin import tseytin_transformation

        return tseytin_transformation(circuit)

    def __init__(self, cnf: tp.Optional[CnfRaw] = None):
        """

        :param cnf: CNF can be not assigned, it means cnf is empty.
        """
        if cnf is None:
            self._cnf = []
        else:
            self._cnf = cnf

    def add_clause(self, clause: Clause):
        """
        Add clause to CNF.

        :param clause: new clause.

        """
        self._cnf.append(clause)

    def get_raw(self) -> CnfRaw:
        """Returns CnfRaw object."""
        return self._cnf
