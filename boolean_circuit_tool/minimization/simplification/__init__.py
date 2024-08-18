"""
Subpackage contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

from .cleanup import cleanup
from .merge_duplicate_gates import MergeDuplicateGates
from .merge_equivalent_gates import MergeEquivalentGates
from .merge_unary_operators import MergeUnaryOperators
from .remove_redundant_gates import RemoveRedundantGates


__all__ = [
    'RemoveRedundantGates',
    'MergeDuplicateGates',
    'MergeEquivalentGates',
    'MergeUnaryOperators',
    'cleanup',
]
