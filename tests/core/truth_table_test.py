import random

import numpy as np

import pytest
from boolean_circuit_tool.core.truth_table import TruthTable


def generate_random_truth_table(input_size: int, output_size: int) -> list[list[bool]]:
    values = np.random.choice(a=[False, True], size=(output_size, 2**input_size))
    return [list(v) for v in values]


def test_evaluate():
    check_evaluate_by_size(3, 3)
    check_evaluate_by_size(5, 2)
    check_evaluate_by_size(6, 1)
    check_evaluate_by_size(7, 1)


def check_evaluate_by_size(input_size: int, output_size: int):
    values = generate_random_truth_table(input_size, output_size)
    truth_table = TruthTable(values)
    values = np.array(values).T.tolist()
    for i in range(2**input_size):
        input_str = bin(i)[2:]
        input_str = '0' * (input_size - len(input_str)) + input_str
        input_values = list(map(lambda x: bool(int(x)), list(input_str)))
        assert values[i] == truth_table.evaluate(input_values)


def test_is_out_constant():
    check_is_out_constant_by_size(3)
    check_is_out_constant_by_size(4)
    check_is_out_constant_by_size(5)
    check_is_out_constant_by_size(6)
    check_is_out_constant_by_size(7)


def check_is_out_constant_by_size(input_size: int):
    constant_out = [False] * (2**input_size)
    truth_table = TruthTable([constant_out])
    assert truth_table.is_out_constant(0)
    assert truth_table.is_constant()


def test_is_out_monotonic():
    check_is_out_monotonic_by_size(3)
    check_is_out_monotonic_by_size(4)
    check_is_out_monotonic_by_size(5)
    check_is_out_monotonic_by_size(6)
    check_is_out_monotonic_by_size(7)


def check_is_out_monotonic_by_size(input_size: int):
    false_count = random.randint(0, 2**input_size)
    monotonic_out = [False] * false_count + [True] * (2**input_size - false_count)
    truth_table = TruthTable([monotonic_out])
    assert truth_table.is_out_monotonic(0)
    assert truth_table.is_monotonic()


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
    assert truth_table.get_out_significant_inputs(0) == mask


def test_is_out_dependent_from_input():
    input_size = 6
    mask = [0, 1, 4]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    for i in range(input_size):
        assert truth_table.is_out_dependent_from_input(0, i) == (i in mask)


def test_get_out_is_input_negation():
    input_size = 3
    mask = [1]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    assert truth_table.get_out_is_input_negation(0, 1) == 0


def test_is_out_symmetric():
    negations = [False, True, True, False, True]
    out = generate_sum(5, negations)
    truth_table = TruthTable([out])
    neg = truth_table.get_out_symmetric_and_negations([0])
    assert neg is not None
    assert neg == negations
