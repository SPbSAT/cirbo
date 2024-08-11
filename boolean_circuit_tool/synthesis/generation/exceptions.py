"""Module defines exceptions related to generation."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'PairwiseXorDifferentShapesError',
    'PairwiseIfThenElseDifferentShapesError',
]


class PairwiseXorDifferentShapesError(BooleanCircuitToolError):
    """Error occurring while constructing pairwise xor for lists of different sizes."""

    pass


class PairwiseIfThenElseDifferentShapesError(BooleanCircuitToolError):
    """Error occurring while constructing pairwise if then else for lists of different
    sizes."""

    pass
