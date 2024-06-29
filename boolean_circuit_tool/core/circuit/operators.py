"""
Functions that evaluate different operators.

(!) Since not is reserved in python, an underscore was added to the function name (not_)
to evaluate this operator, and for consistency, an underscore was added to all other
functions too

"""

import functools
import operator


# TODO нужно ли поддерживать UNDEFINED ?

__all__ = [
    'not_',
    'and_',
    'nand_',
    'or_',
    'nor_',
    'xor_',
    'nxor_',
    'iff_',
]


def not_(arg: bool) -> bool:
    return not arg


def and_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return all((arg1, arg2, *args))


def nand_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return not_(and_(arg1, arg2, *args))


def or_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return any((arg1, arg2, *args))


def nor_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return not_(or_(arg1, arg2, *args))


def xor_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return functools.reduce(operator.xor, (arg1, arg2, *args))


def nxor_(arg1: bool, arg2: bool, *args: bool) -> bool:
    return not_(xor_(arg1, arg2, *args))


def iff_(arg: bool) -> bool:
    return arg
