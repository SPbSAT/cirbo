"""Module defines common core utilities."""

import typing as tp


__all__ = [
    'input_to_canonical_index',
    'canonical_index_to_input',
    'get_bit_value',
]


def input_to_canonical_index(inputs: tp.Iterable[bool]) -> int:
    """
    Get index by input value sequence.

    :param inputs: input value sequence.
    :return: index of provided input sequence in canonical input enumeration.

    Note: canonical input enumeration is achieved by listing unsigned numbers
    given in a big-endian binary encoding ([0, ..., 0, 0], [0, ..., 0, 1],
    [0, ..., 1, 0], [0, ..., 1, 1], ..., [1, ..., 1, 1]), where `i`th bit
    represents value of `i`th input.

    """
    return int(''.join(str(int(v)) for v in inputs), 2)


def canonical_index_to_input(index: int, input_size: int) -> tp.Sequence[bool]:
    """
    Get input value sequence by index.

    :param index: index in canonical input enumeration.
    :param input_size: count of inputs.
    :return: input value sequence.

    Note: canonical input enumeration is achieved by listing unsigned numbers
    given in a big-endian binary encoding ([0, ..., 0, 0], [0, ..., 0, 1],
    [0, ..., 1, 0], [0, ..., 1, 1], ..., [1, ..., 1, 1]), where `i`th bit
    represents value of `i`th input.

    """
    s = bin(index)[2:]
    s = '0' * (input_size - len(s)) + s
    return [bool(int(c)) for c in s]


def get_bit_value(value: int, bit_idx: int) -> bool:
    """
    :param value: some integer value.
    :param bit_idx: big-endian index of bit.
    :return: `bit_idx`th index of number `value`.
    """
    return bool((value & (1 << bit_idx)) >> bit_idx)
