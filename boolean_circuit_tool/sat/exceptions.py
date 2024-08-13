"""Module defines exceptions related to sat."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'MiterDifferentShapesError',
]


class MiterDifferentShapesError(BooleanCircuitToolError):
    """Error occurring in the miter function when the number of inputs or the number of
    outputs in the provided circuits differ."""

    pass
