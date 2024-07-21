import itertools
import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import CircuitElementIsAbsentError

from boolean_circuit_tool.core.circuit.gate import Label

__all__ = [
    'input_iterator_with_fixed_sum',
    'order_list',
]


def input_iterator_with_fixed_sum(
    input_size: int,
    number_of_true: int,
    *,
    negations: tp.Optional[list[bool]] = None,
) -> tp.Iterable:
    """
    Returns all permutations with a given number of True without repetition.

    :param inp: list of assign inputs
    :param number_of_true: the amount of True that will be present in the assign
    :return: assignment inputs as Iterator

    """
    _negations = [False] * input_size if negations is None else negations
    _inp = [False] * input_size
    for indexes in itertools.combinations(range(input_size), number_of_true):
        for idx in range(input_size):
            _inp[idx] = False ^ _negations[idx]
        for idx in indexes:
            _inp[idx] = True ^ _negations[idx]
        yield _inp


def order_list(
    ordered_list: list[Label],
    old_list: list[Label],
) -> list[Label]:
    """
    Order old elements list with full or partially ordered elements list.

    Creates new list by copying `ordered_list`, then appends to it elements
    of `old_list` which are yet absent in resulting list.

    `ordered_list` must be subset of `old_list`.

    """
    new_list = list()
    for elem in ordered_list:
        if elem not in old_list:
            raise CircuitElementIsAbsentError()
        new_list.append(elem)

    if len(new_list) == len(old_list):
        return new_list

    for elem in old_list:
        if elem not in new_list:
            new_list.append(elem)

    return new_list
