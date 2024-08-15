import functools
import logging

from boolean_circuit_tool.core.circuit import Circuit
from .collapse_equivalent_gates import collapse_equivalent_gates
from .collapse_unary_operators import collapse_unary_operators
from .remove_redundant_gates import remove_redundant_gates


__all__ = [
    'cleanup',
]

logger = logging.getLogger(__name__)


def cleanup(circuit: Circuit) -> Circuit:
    """
    Applies several simplification algorithms from this module consecutively in order to
    simplify provided circuit.

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

    """
    return functools.reduce(
        lambda _circ, _method: _method(_circ),  # type: ignore
        [
            remove_redundant_gates,
            collapse_unary_operators,
            remove_redundant_gates,
            collapse_equivalent_gates,
            remove_redundant_gates,
        ],
        circuit,
    )
