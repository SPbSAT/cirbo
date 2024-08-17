import logging

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.transformer import Transformer


__all__ = [
    'CollapseDuplicateGates',
]


logger = logging.getLogger(__name__)


class CollapseDuplicateGates(Transformer):
    def _transform(self, circuit: Circuit) -> Circuit:
        """
        Finds literal duplicates (gates which have same type and operands) and relink
        their users to only one of them.

        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        return circuit
