import typing as tp

from cirbo.core.exceptions import DontCareCastError


__all__ = [
    'DontCare',
    'TriValue',
]


class _DontCare:
    """Class of object, which represents "don't care" value, meaning that this value is
    yet to be determined."""

    def __bool__(self):
        raise DontCareCastError(
            "Bool can't be created from DontCare. "
            "Possibly function model is used in context "
            "where full defined function is needed."
        )

    def __eq__(self, rhs):
        return isinstance(rhs, _DontCare)

    def __hash__(self):
        return hash(self.__class__.__name__)


# To be similar to False and True.
# Represents indeterminate state (of output) which can
# be either False or True depending on condition definition.
DontCare = _DontCare()

TriValue = tp.Union[bool, _DontCare]
