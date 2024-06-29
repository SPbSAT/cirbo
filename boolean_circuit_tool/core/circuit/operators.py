"""
Functions that evaluate different operators.

(!) Since not is reserved in python, an underscore was added to the function name (not_)
to evaluate this operator, and for consistency, an underscore was added to all other
functions too

"""

import enum
import functools

__all__ = [
    'GateAssign',
    'iff_',
    'not_',
    'and_',
    'nand_',
    'or_',
    'nor_',
    'xor_',
    'nxor_',
]


class GateAssign(enum.Enum):
    FALSE = 0
    TRUE = 1
    UNDEFINED = 2


GateStateNumber: int = 3


def iff_(arg: GateAssign) -> GateAssign:
    return [
        GateAssign.FALSE,  # arg = GateAssign.FALSE
        GateAssign.TRUE,  # arg = GateAssign.TRUE
        GateAssign.UNDEFINED,  # arg = GateAssign.UNDEFINED
    ][arg.value]


def not_(arg: GateAssign) -> GateAssign:
    return [
        GateAssign.TRUE,  # arg = GateAssign.FALSE
        GateAssign.FALSE,  # arg = GateAssign.TRUE
        GateAssign.UNDEFINED,  # arg = GateAssign.UNDEFINED
    ][arg.value]


def _and(arg1: GateAssign, arg2: GateAssign) -> GateAssign:
    return [
        GateAssign.FALSE,  # arg1 = GateAssign.FALSE
        GateAssign.FALSE,
        GateAssign.FALSE,
        GateAssign.FALSE,  # arg1 = GateAssign.TRUE
        GateAssign.TRUE,
        GateAssign.UNDEFINED,
        GateAssign.FALSE,  # arg1 = GateAssign.UNDEFINED
        GateAssign.UNDEFINED,
        GateAssign.UNDEFINED,
    ][arg1.value * GateStateNumber + arg2.value]


def and_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return functools.reduce(_and, (arg1, arg2, *args))


def nand_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return not_(and_(arg1, arg2, *args))


def _or(arg1: GateAssign, arg2: GateAssign) -> GateAssign:
    return [
        GateAssign.FALSE,  # arg1 = GateAssign.FALSE
        GateAssign.TRUE,
        GateAssign.UNDEFINED,
        GateAssign.TRUE,  # arg1 = GateAssign.TRUE
        GateAssign.TRUE,
        GateAssign.TRUE,
        GateAssign.UNDEFINED,  # arg1 = GateAssign.UNDEFINED
        GateAssign.TRUE,
        GateAssign.UNDEFINED,
    ][arg1.value * GateStateNumber + arg2.value]


def or_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return functools.reduce(_or, (arg1, arg2, *args))


def nor_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return not_(or_(arg1, arg2, *args))


def _xor(arg1: GateAssign, arg2: GateAssign) -> GateAssign:
    return [
        GateAssign.FALSE,  # arg1 = GateAssign.FALSE
        GateAssign.TRUE,
        GateAssign.UNDEFINED,
        GateAssign.TRUE,  # arg1 = GateAssign.TRUE
        GateAssign.FALSE,
        GateAssign.UNDEFINED,
        GateAssign.UNDEFINED,  # arg1 = GateAssign.UNDEFINED
        GateAssign.UNDEFINED,
        GateAssign.UNDEFINED,
    ][arg1.value * GateStateNumber + arg2.value]


def xor_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return functools.reduce(_xor, (arg1, arg2, *args))


def nxor_(arg1: GateAssign, arg2: GateAssign, *args: GateAssign) -> GateAssign:
    return not_(xor_(arg1, arg2, *args))
