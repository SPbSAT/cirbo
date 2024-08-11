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
    return [bool(int(c)) for c in s][-input_size::]


def get_bit_value(value: int, bit_idx: int, bit_size: int) -> bool:
    """
    :param value: some integer value.
    :param bit_idx: little-endian index of bit. Since leftmost element of input is
           considered to set 0'th input value this method will return `bit_idx`th
           bit of `value` in little-endian order which corresponds to `bit_idx`th
           input value.
    :param bit_size: number of bits in the given integer.
    :return: `bit_idx`th index of number `value`.
    """
    _shift = bit_size - bit_idx - 1
    return bool((value & (1 << _shift)) >> _shift)
