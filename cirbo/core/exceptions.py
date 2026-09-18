"""Module defines exceptions related to core objects, e.g. Circuit."""

from cirbo.exceptions import CirboError

__all__ = [
    'BooleanModelError',
    'BooleanFunctionError',
    'BadDefinitionError',
    'DontCareCastError',
    'BadBooleanValue',
    'BadBooleanValue',
    'TruthTableBadShapeError',
    'BadCallableError',
    'TruthTableNormalizationError',
]


class BooleanModelError(CirboError):
    """Base for FunctionModel protocol general class of exceptions."""

    pass


class BooleanFunctionError(CirboError):
    """Base for Function protocol general class of exceptions."""

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


class BadCallableError(CirboError):
    """Represents error raised provided unsupported callable to PyFunction."""

    pass


class TruthTableNormalizationError(CirboError):
    """Represents error raised when a truth table cannot be normalized, or when a
    circuit cannot be denormalized because it does not match the normalization it is
    given to."""

    pass

