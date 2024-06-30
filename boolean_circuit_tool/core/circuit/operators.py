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
    'iff_',
    'not_',
    'and_',
    'nand_',
    'or_',
    'nor_',
    'xor_',
    'nxor_',
]


class _Undefined:
    def __bool__(self):
        raise GateStateError("Bool can't be created from Undefined state.")

    def __eq__(self, rhs):
        return isinstance(rhs, _Undefined)

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


_and: list[GateState] = [
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
        lambda p1, p2: _and[
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


_xor: list[GateState] = [
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
        lambda p1, p2: _xor[
            index_from_state(p1) * GateStateNumber + index_from_state(p2)
        ],
        (arg1, arg2, *args),
    )


def nxor_(arg1: GateState, arg2: GateState, *args: GateState) -> GateState:
    return not_(xor_(arg1, arg2, *args))
