import functools
import logging

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.transformer import Transformer
from .collapse_equivalent_gates import CollapseEquivalentGates
from .collapse_unary_operators import CollapseUnaryOperators
from .remove_redundant_gates import RemoveRedundantGates


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
    return Transformer.apply_transformers(
        circuit,
        [
            RemoveRedundantGates(),
            CollapseUnaryOperators(),
            CollapseEquivalentGates(),
        ],
    )
