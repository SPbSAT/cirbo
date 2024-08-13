"""Module defines exceptions related to generation."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'BadShapesError',
    'DifferentShapesError',
    'BadBasisError',
    'PairwiseXorDifferentShapesError',
    'PairwiseIfThenElseDifferentShapesError',
]


class BadShapesError(BooleanCircuitToolError):
    """Error that occurs when constructing some circuit with bad connecting gates."""

    pass


class DifferentShapesError(BadShapesError):
    """Error that occurs when constructing some circuit with badly given shapes of
    inputs or outputs."""

    pass


class BadBasisError(BooleanCircuitToolError):
    """Error that occurs when generation method is given a bad basis."""

    pass


class PairwiseXorDifferentShapesError(DifferentShapesError):
    """Error that occurs when constructing pairwise xor for lists of different sizes."""

    pass


class PairwiseIfThenElseDifferentShapesError(DifferentShapesError):
    """Error that occurs when constructing pairwise if then else for lists of different
    sizes."""

    pass
