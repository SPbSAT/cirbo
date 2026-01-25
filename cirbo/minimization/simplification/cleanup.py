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


def cleanup(circuit: Circuit, *, use_heavy: bool = False) -> Circuit:
    """
    Applies several simplification algorithms from this module consecutively in order to
    simplify provided circuit.

    :param circuit: the original circuit to be simplified
    :param use_heavy: if True, then heavier cleanups (e.g. `MergeEquivalentGates`)
           will also be used.
    :return: new simplified version of the circuit

    """
    _strategies = [
        RemoveRedundantGates(),
        MergeUnaryOperators(),
        MergeDuplicateGates(),
    ]

    if use_heavy:
        _strategies += [MergeEquivalentGates()]

    return Transformer.apply_transformers(
        circuit,
        _strategies,
    )
