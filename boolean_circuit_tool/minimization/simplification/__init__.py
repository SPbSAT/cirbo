"""
Subpackage contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

from .cleanup import cleanup
from .collapse_equivalent_gates import CollapseEquivalentGates
from .collapse_unary_operators import CollapseUnaryOperators
from .remove_redundant_gates import RemoveRedundantGates


__all__ = [
    'RemoveRedundantGates',
    'CollapseUnaryOperators',
    'cleanup',
]
