import random
import typing as tp

import pytest
from boolean_circuit_tool.core.boolean_function import RawTruthTable

from boolean_circuit_tool.core.exceptions import (
    BadBooleanValue,
    TruthTableBadShapeError,
)
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.core.truth_table import (
    _parse_bool,
    _parse_trival,
    _str_to_bool,
    _str_to_trival,
    TruthTable,
    TruthTableModel,
)


def generate_random_truth_table(input_size: int, output_size: int) -> RawTruthTable:
    return [
        [random.choice([True, False]) for _ in range(2**input_size)]
        for _ in range(output_size)
    ]


@pytest.mark.parametrize(
    'x, expected',
    [
        ('0', False),
        ('1', True),
    ],
)
def test_str_to_bool(x, expected):
    assert _str_to_bool(x) == expected


@pytest.mark.parametrize(
    'x',
    [
        '*',
        'abc',
        '123',
        '',
    ],
)
def test_str_to_bool_raises(x):
    with pytest.raises(BadBooleanValue):
        _ = _str_to_bool(x)


@pytest.mark.parametrize(
    'x, expected',
    [
        ('0', False),
        ('1', True),
        ('*', DontCare),
    ],
)
def test_str_to_trival(x, expected):
    assert _str_to_trival(x) == expected


@pytest.mark.parametrize(
    'x',
    [
        'abc',
        '123',
        '',
    ],
)
def test_str_to_bool_trival(x):
    with pytest.raises(BadBooleanValue):
        _ = _str_to_trival(x)


@pytest.mark.parametrize(
    'x, expected',
    [
        (0, False),
        (1, True),
        (False, False),
        (True, True),
        ('0', False),
        ('1', True),
    ],
)
def test_parse_bool(x, expected):
    assert _parse_bool(x) == expected


@pytest.mark.parametrize(
    'x, expected',
    [
        (0, False),
        (1, True),
        (False, False),
        (True, True),
        (DontCare, DontCare),
        ('0', False),
        ('1', True),
        ('*', DontCare),
    ],
)
def test_parse_trival(x, expected):
    assert _parse_trival(x) == expected


@pytest.mark.parametrize(
    'arg_tt, expected_tt, expected_transposed_tt',
    [
        (
            [[False, True, '1', '1'], '0010'],
            [[False, True, True, True], [False, False, True, False]],
            [[False, False], [True, False], [True, True], [True, False]],
        ),
        (
            ['00000001'],
            [[False, False, False, False, False, False, False, True]],
            [[False], [False], [False], [False], [False], [False], [False], [True]],
        ),
    ],
)
def test_truth_table_initialization(arg_tt, expected_tt, expected_transposed_tt):
    tt = TruthTable(arg_tt)
    assert tt.get_truth_table() == expected_tt
    assert tt._table_t == expected_transposed_tt


@pytest.mark.parametrize(
    'arg_tt, expected_model_tt, expected_transposed_model_tt',
    [
        (
            [[False, DontCare, '*', '1'], '0*10'],
            [[False, DontCare, DontCare, True], [False, DontCare, True, False]],
            [[False, False], [DontCare, DontCare], [DontCare, True], [True, False]],
        ),
    ],
)
def test_truth_table_model_initialization(
    arg_tt,
    expected_model_tt,
    expected_transposed_model_tt,
):
    tt = TruthTableModel(arg_tt)
    assert tt.get_model_truth_table() == expected_model_tt
    assert tt._table_t == expected_transposed_model_tt


@pytest.mark.parametrize(
    'raw_tt, exc',
    [
        ([[True, True, False], [True, True]], TruthTableBadShapeError),
        ([[True, 'A'], [False, False]], BadBooleanValue),
        ([[True, True], [15, False]], BadBooleanValue),
    ],
)
def test_bad_tt_arg_raises(raw_tt, exc):
    with pytest.raises(exc):
        _ = TruthTable(raw_tt)


@pytest.mark.parametrize(
    'raw_tt, exc',
    [
        ([[DontCare, True, False], [True, True]], TruthTableBadShapeError),
        ([[DontCare, 'A'], [DontCare, False]], BadBooleanValue),
        ([[DontCare, True], [7, False]], BadBooleanValue),
    ],
)
def test_bad_tt_arg_model_raises(raw_tt, exc):
    with pytest.raises(exc):
        _ = TruthTableModel(raw_tt)


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


def test_is_constant_simple():
    tt = TruthTable(['0000', '1101'])
    assert tt.is_constant_at(0)
    assert not tt.is_constant_at(1)
    assert not tt.is_constant()


@pytest.mark.parametrize("input_size", [3, 4, 5, 6, 7])
def test_is_out_constant(input_size: int):
    constant_out = [False] * (2**input_size)
    truth_table = TruthTable([constant_out])
    assert truth_table.is_constant_at(0)
    assert truth_table.is_constant()


def test_is_monotonic_simple():
    tt = TruthTable(['1110', '0001'])
    assert not tt.is_monotonic_at(0, inverse=False)
    assert tt.is_monotonic_at(1, inverse=False)
    assert not tt.is_monotonic(inverse=False)
    assert tt.is_monotonic_at(0, inverse=True)
    assert not tt.is_monotonic_at(1, inverse=True)
    assert not tt.is_monotonic(inverse=True)


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


def test_is_output_equal_to_input():
    tt1 = TruthTable(['0101'])
    assert tt1.is_output_equal_to_input(0, 1)
    tt2 = TruthTable(['1010'])
    assert not tt2.is_output_equal_to_input(0, 1)


def test_is_output_equal_to_input_negation():
    tt1 = TruthTable(['1010'])
    assert tt1.is_output_equal_to_input_negation(0, 1)
    tt2 = TruthTable(['0010'])
    assert not tt2.is_output_equal_to_input_negation(0, 1)


def test_is_symmetric():
    tt1 = TruthTable(['00000000', '00000000'])
    assert tt1.is_symmetric()
    assert tt1.is_symmetric_at(0)
    assert tt1.is_symmetric_at(1)
    tt2 = TruthTable(['0110', '1001'])
    assert tt2.is_symmetric()
    assert tt2.is_symmetric_at(0)
    assert tt2.is_symmetric_at(1)
    tt3 = TruthTable(['0100', '1001'])
    assert not tt3.is_symmetric()
    assert not tt3.is_symmetric_at(0)
    assert tt3.is_symmetric_at(1)


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
