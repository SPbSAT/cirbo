import random
import typing as tp

import pytest

from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.core.boolean_function import RawTruthTable
from boolean_circuit_tool.core.truth_table import TruthTable, TruthTableModel


def generate_random_truth_table(input_size: int, output_size: int) -> RawTruthTable:
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
    assert truth_table.is_monotonic_at(0, inverse=False)
    assert truth_table.is_monotonic(inverse=False)


def generate_sum(
    input_size: int, negations: tp.Optional[list[bool]] = None
) -> list[bool]:
    lst = []
    for i in range(2**input_size):
        b = bin(i)[2:]  # type: ignore
        b = '0' * (input_size - len(b)) + b  # type: ignore
        b = [int(v) for v in b]  # type: ignore
        if negations is not None:
            b = [b[i] ^ negations[i] for i in range(len(b))]  # type: ignore
        s = b.count(1)  # type: ignore
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
        assert truth_table.is_dependent_on_input_at(0, i) == (i in mask)


def test_get_out_is_input_negation():
    input_size = 3
    mask = [1]
    out = generate_out_by_mask(input_size, mask)
    truth_table = TruthTable([out])
    assert truth_table.is_output_equal_to_input(0, 1)
    assert not truth_table.is_output_equal_to_input_negation(0, 1)


def test_is_out_symmetric():
    negations = [False, True, True, False, True]
    out = generate_sum(5, negations)
    truth_table = TruthTable([out])
    neg = truth_table.find_negations_to_make_symmetric([0])
    assert neg is not None
    assert neg == negations


class TestTruthTableModel:
    simple_model = TruthTableModel(
        table=[[False, DontCare, True, DontCare]],
    )
    two_output_model = TruthTableModel(
        table=[
            [True, True, DontCare, DontCare],
            [DontCare, False, True, False],
        ],
    )

    def test_model_shape(self):
        assert self.simple_model.input_size == 2
        assert self.simple_model.output_size == 1
        assert self.two_output_model.input_size == 2
        assert self.two_output_model.output_size == 2

    def test_model_checks(self):
        assert self.simple_model.check([True, False]) == [True]
        assert self.simple_model.check([True, True]) == [DontCare]
        assert self.simple_model.check_at([True, True], 0) == DontCare

        assert self.two_output_model.check([False, False]) == [True, DontCare]
        assert self.two_output_model.check_at([False, False], 1) == DontCare

    @pytest.mark.parametrize(
        'model, expected',
        [
            pytest.param(
                simple_model,
                [[False, DontCare, True, DontCare]],
                id='simple model',
            ),
            pytest.param(
                two_output_model,
                [
                    [True, True, DontCare, DontCare],
                    [DontCare, False, True, False],
                ],
                id='two output model',
            ),
        ],
    )
    def test_get_model_truth_table(self, model: TruthTableModel, expected: list):
        assert model.get_model_truth_table() == expected

    @pytest.mark.parametrize(
        'model, definition, expected',
        [
            pytest.param(
                simple_model,
                {
                    ((False, True), 0): True,
                    ((True, True), 0): False,
                },
                [[False, True, True, False]],
                id='simple model',
            ),
            pytest.param(
                two_output_model,
                {
                    ((True, False), 0): False,
                    ((True, True), 0): True,
                    ((False, False), 1): False,
                },
                [
                    [True, True, False, True],
                    [False, False, True, False],
                ],
                id='two output model',
            ),
        ],
    )
    def test_model_define(
        self, model: TruthTableModel, definition: dict, expected: list
    ):
        tt = model.define(definition=definition)
        assert tt.get_truth_table() == expected
