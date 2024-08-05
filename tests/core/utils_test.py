import pytest

from boolean_circuit_tool.core.utils import get_bit_value, input_to_canonical_index


@pytest.mark.parametrize(
    'bit_list, expected',
    (
        ([0], 0),
        ([1], 1),
        ([0, 0], 0),
        ([0, 1], 1),
        ([1, 0], 2),
        ([1, 1], 3),
        ([1, 0, 1, 0], 10),
        ([0, 1, 1, 0], 6),
        ([1, 1, 1, 0, 0, 0], 56),
        ([0, 1, 1, 0, 0, 1], 25),
        ([1, 0, 1, 0, 1, 0, 1, 0], 170),
    ),
)
def test_input_to_canonical_index(bit_list: list[bool], expected: int):
    assert input_to_canonical_index(bit_list) == expected


@pytest.mark.parametrize(
    'bit_list',
    (
        [0],
        [1],
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [1, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 0],
    ),
)
def test_get_bit_value(bit_list: list[bool]):
    value = input_to_canonical_index(bit_list)
    for idx, bit in enumerate(bit_list):
        assert get_bit_value(value, bit_idx=idx, bit_size=len(bit_list)) == bit
