"""Module defines exceptions related to sat."""

from cirbo.exceptions import CirboError

__all__ = [
    'MiterDifferentShapesError',
]


class MiterDifferentShapesError(CirboError):
    """Error occurring in the miter function when the number of inputs or the number of
    outputs in the provided circuits differ."""

    pass
