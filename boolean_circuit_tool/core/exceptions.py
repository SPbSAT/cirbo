"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'BooleanModelError',
    'BooleanFunctionError',
    'BadDefinitionError',
    'DontCareCastError',
    'BadBooleanValue',
    'BadBooleanValue',
    'TruthTableBadShapeError',
]


class BooleanModelError(BooleanCircuitToolError):
    """Base for BooleanFunctionModel protocol general class of exceptions."""

    pass


class BooleanFunctionError(BooleanCircuitToolError):
    """Base for BooleanFunction protocol general class of exceptions."""

    pass


class BadDefinitionError(BooleanModelError):
    """Represents error raised when boolean model is given a bad definition."""

    pass


class DontCareCastError(BooleanModelError):
    """Represents error raised when `DontCare` is being cast to bool."""

    pass


class BadBooleanValue(BooleanModelError):
    """Represents error raised when value can't be parsed as boolean or trival."""

    pass


class TruthTableBadShapeError(BooleanModelError):
    """Represents error raised when given truth table has bad shape."""

    pass
