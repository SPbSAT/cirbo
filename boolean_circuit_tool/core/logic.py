import typing as tp

from boolean_circuit_tool.core.exceptions import BooleanModelError


__all__ = [
    'DontCareCastError',
    'DontCare',
    'TriValue',
]


class DontCareCastError(BooleanModelError):
    """Represents error raised when `DontCare` is being cast to bool."""

    pass


class _DontCare:
    def __bool__(self):
        raise DontCareCastError("Bool can't be created from DontCare.")

    def __eq__(self, rhs):
        return isinstance(rhs, _DontCare)

    def __hash__(self):
        return hash(self.__class__.__name__)


# To be similar to False and True.
# Represents indeterminate state (of output) which can
# be either False or True depending on condition definition.
DontCare = _DontCare()

TriValue = tp.Union[bool, _DontCare]
