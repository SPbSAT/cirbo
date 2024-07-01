import random

import pytest
import numpy as np
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
    for i in range(2 ** input_size):
        input_str = bin(i)[2:]
        input_str = '0' * (input_size - len(input_str)) + input_str
        input_values = list(map(lambda x: bool(int(x)), list(input_str)))
        assert values[i] == truth_table.evaluate(input_values)


def test_is_out_constant():
    check_is_out_constant_by_size(3, 3)
    check_is_out_constant_by_size(5, 1)
    check_is_out_constant_by_size(6, 2)
    check_is_out_constant_by_size(7, 2)


def check_is_out_constant_by_size(input_size: int, output_size: int):
    constant_out = [False] * (2 ** input_size)
    outs = generate_random_truth_table(input_size, output_size - 1)
    outs.append(constant_out)
    truth_table = TruthTable(outs)
    for i in range(output_size - 1):
        assert not truth_table.is_out_constant(i)
    assert truth_table.is_out_constant(output_size - 1)


def check_is_out_monotonic_by_size(input_size: int, output_size: int):
    false_count = random.randint(0, 2**input_size)
    monotonic_out = [False] * false_count + [True] * (2**input_size - false_count)
    outs = generate_random_truth_table(input_size, output_size - 1)
    outs.append(monotonic_out)
    truth_table = TruthTable(outs)
    for i in range(output_size - 1):
        assert not truth_table.is_out_monotonic(i)
    assert truth_table.is_out_monotonic(output_size - 1)