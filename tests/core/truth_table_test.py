import random

import pytest

from boolean_circuit_tool.core.truth_table import TruthTable


def generate_random_truth_table(input_size: int, output_size: int) -> list[list[bool]]:
    return [
        [random.choice([True, False]) for _ in range(2**input_size)]
        for _ in range(output_size)
    ]


@pytest.mark.parametrize("input_size, output_size", [(3, 3), (5, 2), (6, 1), (7, 1)])
def test_evaluate(input_size: int, output_size: int):
    values = generate_random_truth_table(input_size, output_size)
    truth_table = TruthTable(values)
    values = [list(i) for i in zip(*values)]
    for i in range(2**input_size):
        input_str = bin(i)[2:]
        input_str = '0' * (input_size - len(input_str)) + input_str
        input_values = list(map(lambda x: bool(int(x)), list(input_str)))
        assert values[i] == truth_table.evaluate(input_values)


@pytest.mark.parametrize("input_size", [3, 4, 5, 6, 7])
def test_is_out_constant(input_size: int):
    constant_out = [False] * (2**input_size)
    truth_table = TruthTable([constant_out])
    assert truth_table.is_constant_at(0)
    assert truth_table.is_constant()


@pytest.mark.parametrize("input_size", [3, 4, 5, 6, 7])
def test_is_out_monotonic(input_size: int):
    false_count = random.randint(0, 2**input_size)
    monotonic_out = [False] * false_count + [True] * (2**input_size - false_count)
    truth_table = TruthTable([monotonic_out])
    assert truth_table.is_monotonic_at(0, False)
    assert truth_table.is_monotonic(False)


def generate_sum(input_size: int, negations: list[bool] = None) -> list[bool]:
    lst = []
    for i in range(2**input_size):
        b = bin(i)[2:]
        b = '0' * (input_size - len(b)) + b
        b = [int(v) for v in b]
        if negations is not None:
            b = [b[i] ^ negations[i] for i in range(len(b))]
        s = b.count(1)
        lst.append(s > input_size / 2)
    return lst


def generate_out_by_mask(input_size: int, mask: list[int]) -> list[bool]:
    s = generate_sum(len(mask))
    out = []
    for i in range(2**input_size):
        st = bin(i)[2:]
        st = '0' * (input_size - len(st)) + st
        idx = int(''.join([st[j] for j in mask]), 2)
        out.append(s[idx])
    return out


def test_get_significant_inputs():
    input_size = 6
    mask = [0, 1, 4]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    assert truth_table.get_significant_inputs_of(0) == mask


def test_is_out_dependent_from_input():
    input_size = 6
    mask = [0, 1, 4]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    for i in range(input_size):
        assert truth_table.is_dependent_from_input_of(0, i) == (i in mask)


def test_get_out_is_input_negation():
    input_size = 3
    mask = [1]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    assert truth_table.get_out_as_input_negation(0, 1) == 0


def test_is_out_symmetric():
    negations = [False, True, True, False, True]
    out = generate_sum(5, negations)
    truth_table = TruthTable([out])
    neg = truth_table.get_symmetric_and_negations_of([0])
    assert neg is not None
    assert neg == negations
