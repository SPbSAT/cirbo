"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'BooleanModelError',
    'BooleanFunctionError',
    'BadDefinitionError',
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
