"""
Functions that evaluate different operators.

(!) Since not is reserved in python, an underscore was added to the function name (not_)
to evaluate this operator, and for consistency, an underscore was added to all other
functions too

"""

import functools
import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import GateStateError

__all__ = [
    'GateState',
    'Undefined',
    'always_false_',
    'always_true_',
    'and_',
    'geq_',
    'gt_',
    'iff_',
    'leq_',
    'liff_',
    'lnot_',
    'lt_',
    'nand_',
    'nor_',
    'not_',
    'nxor_',
    'or_',
    'riff_',
    'rnot_',
    'xor_',
]


class _Undefined:
    def __bool__(self):
        raise GateStateError("Bool can't be created from Undefined state.")

    def __eq__(self, rhs):
        return isinstance(rhs, _Undefined)

    def __lt__(self, rhs):
        raise GateStateError("Undefined state haven't order relative to bool")

    def __le__(self, rhs):
        raise GateStateError("Undefined state haven't order relative to bool")

    def __gt__(self, rhs):
        raise GateStateError("Undefined state haven't order relative to bool")

    def __ge__(self, rhs):
        raise GateStateError("Undefined state haven't order relative to bool")

    def __hash__(self):
        return hash('Undefined')


# To be similar to False and True.
Undefined = _Undefined()

GateState = tp.Union[bool, _Undefined]
GateStateNumber: int = 3

_state_to_index_map: tp.Dict[GateState, int] = {
    False: 0,
    True: 1,
    Undefined: 2,
}


def index_from_state(state: GateState) -> int:
    """
    :return: index of `state` in [False, True, Undefined] array,
             suitable for truth table encodings.

    """
    return _state_to_index_map[state]


_not: list[GateState] = [
    True,  # arg = False
    False,  # arg = True
    Undefined,  # arg = Undefined
]


def not_(arg: GateState) -> GateState:
    return _not[index_from_state(arg)]


def iff_(arg: GateState) -> GateState:
    return arg


_and_truth_table: list[GateState] = [
    False,  # arg1 = False
    False,
    False,
    False,  # arg1 = True
    True,
    Undefined,
    False,  # arg1 = Undefined
    Undefined,
    Undefined,
]


def and_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return functools.reduce(
        lambda p1, p2: _and_truth_table[
            index_from_state(p1) * GateStateNumber + index_from_state(p2)
        ],
        (arg1, arg2, *args),
    )


def nand_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return not_(and_(arg1, arg2, *args))


_or_truth_table: list[GateState] = [
    False,  # arg1 = False
    True,
    Undefined,
    True,  # arg1 = True
    True,
    True,
    Undefined,  # arg1 = Undefined
    True,
    Undefined,
]


def or_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return functools.reduce(
        lambda p1, p2: _or_truth_table[
            index_from_state(p1) * GateStateNumber + index_from_state(p2)
        ],
        (arg1, arg2, *args),
    )


def nor_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return not_(or_(arg1, arg2, *args))


_xor_truth_table: list[GateState] = [
    False,  # arg1 = False
    True,
    Undefined,
    True,  # arg1 = True
    False,
    Undefined,
    Undefined,  # arg1 = Undefined
    Undefined,
    Undefined,
]


def xor_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return functools.reduce(
        lambda p1, p2: _xor_truth_table[
            index_from_state(p1) * GateStateNumber + index_from_state(p2)
        ],
        (arg1, arg2, *args),
    )


def nxor_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return not_(xor_(arg1, arg2, *args))


def always_true_(*args: GateState) -> GateState:
    return True


def always_false_(*args: GateState) -> GateState:
    return False


def rnot_(arg1: GateState, arg2: GateState) -> GateState:
    return not arg2 if arg2 != Undefined else Undefined


def lnot_(arg1: GateState, arg2: GateState) -> GateState:
    return not arg1 if arg1 != Undefined else Undefined


def riff_(arg1: GateState, arg2: GateState) -> GateState:
    return arg2


def liff_(arg1: GateState, arg2: GateState) -> GateState:
    return arg1


def gt_(arg1: GateState, arg2: GateState) -> GateState:
    if arg1 == True:
        return not_(arg2)
    return arg1


def lt_(arg1: GateState, arg2: GateState) -> GateState:
    if arg1 == False:
        return arg2
    return not_(arg1)


def geq_(arg1: GateState, arg2: GateState) -> GateState:
    if arg1 == False:
        return not_(arg2)
    return arg1


def leq_(arg1: GateState, arg2: GateState) -> GateState:
    if arg1 == True:
        return arg2
    return not_(arg1)
