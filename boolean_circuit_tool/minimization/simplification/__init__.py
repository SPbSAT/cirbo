"""
Subpackage contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

from .cleanup import cleanup
from .collapse_equivalent_gates import collapse_equivalent_gates
from .collapse_unary_operators import collapse_unary_operators
from .remove_redundant_gates import remove_redundant_gates


__all__ = [
    'remove_redundant_gates',
    'collapse_unary_operators',
    'cleanup',
]
