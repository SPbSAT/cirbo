import logging

from cirbo.core.circuit import Circuit
from cirbo.core.circuit.transformer import Transformer

from .merge_duplicate_gates import MergeDuplicateGates
from .merge_equivalent_gates import MergeEquivalentGates
from .merge_unary_operators import MergeUnaryOperators
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
            MergeUnaryOperators(),
            MergeDuplicateGates(),
            MergeEquivalentGates(),
        ],
    )
