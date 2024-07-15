import itertools
import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import CircuitElementIsAbsentError

from boolean_circuit_tool.core.circuit.gate import Label

__all__ = [
    'input_iterator',
    'input_iterator_with_negations',
    'sort_list',
]


def input_iterator(inp: list[bool], number_of_true: int) -> tp.Iterable:
    """
    Returns all permutations with a given number of True without repetition.

    :param inp: list of assign inputs
    :param number_of_true: the amount of True that will be present in the assign
    :return: assign inputs as Iterator

    """
    for x in itertools.combinations(range(len(inp)), number_of_true):
        for idx in range(len(inp)):
            inp[idx] = False
        for idx in x:
            inp[idx] = True
        yield inp


def input_iterator_with_negations(
    inp: list[bool],
    number_of_true: int,
    negations: list[bool],
) -> tp.Iterable:
    """
    Returns all permutations with a given number of True without repetition with post-
    applied negation.

    :param inp: list of assign inputs
    :param number_of_true: the amount of True that will be present in the assign
    :param negations: list of negations
    :return: assign inputs with post-applied negation as Iterator

    """
    for x in itertools.combinations(range(len(inp)), number_of_true):
        for idx in range(len(inp)):
            inp[idx] = False ^ negations[idx]
        for idx in x:
            inp[idx] = True ^ negations[idx]
        yield inp


def sort_list(
    sorted_list: list[Label],
    old_list: list[Label],
) -> list[Label]:
    """
    Sort old elements list with full or partially sorted elements list.

    Creates new list by copying `sorted_list`, then appends to it elements
    of `old_list` which are yet absent in resulting list.

    `sorted_list` must be subset of `old_list`.

    """
    new_list = list()
    for elem in sorted_list:
        if elem not in old_list:
            raise CircuitElementIsAbsentError()
        new_list.append(elem)

    if len(new_list) == len(old_list):
        return new_list

    for elem in old_list:
        if elem not in new_list:
            new_list.append(elem)

    return new_list
