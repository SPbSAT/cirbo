import typing as tp

import pytest
from boolean_circuit_tool.core.boolean_function import RawTruthTable
from boolean_circuit_tool.core.logic import DontCare, TriValue

from boolean_circuit_tool.core.python_function import (
    FunctionType,
    PyFunction,
    PyFunctionModel,
)
from boolean_circuit_tool.core.utils import canonical_index_to_input


def f_max(x1: bool, x2: bool, x3: bool) -> tp.Sequence[bool]:
    return [bool(max(x1, x2, x3))]


def f_max_and_min(x1: bool, x2: bool, x3: bool, x4: bool) -> tp.Sequence[bool]:
    return [bool(max(x1, x2, x3, x4)), bool(min(x1, x2, x3, x4))]


def f_const(_: bool, __: bool, ___: bool) -> tp.Sequence[bool]:
    return [False, True]


def sum_inputs(xs: list[bool]) -> tp.Sequence[bool]:
    count = len(xs)
    num = len(bin(count)[2:])
    s = 0
    for x in xs:
        s += int(x)
    s %= count + 1
    return canonical_index_to_input(s, num)


def sum_inputs_with_negations(
    xs: list[bool], negations: list[bool]
) -> tp.Sequence[bool]:
    return sum_inputs([a ^ b for a, b in zip(xs, negations)])


def f_sum(x1: bool, x2: bool, x3: bool) -> tp.Sequence[bool]:
    return sum_inputs([x1, x2, x3])


def f_one_plus_minus(x1: bool, x2: bool) -> tp.Sequence[bool]:
    s = 1 + int(x1) - int(x2)
    b = bin(s)[2:]
    b = '0' * (2 - len(b)) + b
    return [bool(int(c)) for c in b]


def f_arg0_and_arg1(arg0: bool, arg1: bool, _: bool) -> tp.Sequence[bool]:
    return [arg0 and arg1]


def f_arg1_or_arg2(_: bool, arg1: bool, arg2: bool) -> tp.Sequence[bool]:
    return [arg1 or arg2]


def f_arg0_xor_arg2(arg0: bool, _: bool, arg2: bool) -> tp.Sequence[bool]:
    return [arg0 ^ arg2]


def f_arg0(arg0: bool, _: bool, __: bool) -> tp.Sequence[bool]:
    return [arg0]


def f_not_arg0(arg0: bool, _: bool, __: bool) -> tp.Sequence[bool]:
    return [not arg0]


def f_binary_model_0(arg0: bool, arg1: bool) -> tp.Sequence[TriValue]:
    if arg0 is False:
        return [DontCare]
    return [arg0 ^ arg1]


def f_binary_model_1(arg0: bool, arg1: bool) -> tp.Sequence[TriValue]:
    if arg0 is False:
        return [DontCare, arg0 | arg1]
    return [arg0 ^ arg1, DontCare]


class TestPyFunctionModel:
    @pytest.mark.parametrize(
        "model, input_size, output_size",
        [
            (
                f_binary_model_0,
                2,
                1,
            ),
            (
                f_binary_model_1,
                2,
                2,
            ),
        ],
    )
    def test_init(self, model, input_size, output_size):
        py_model = PyFunctionModel(model)
        assert py_model.input_size == input_size
        assert py_model.output_size == output_size

    @pytest.mark.parametrize(
        "model, expected_answers",
        [
            (
                f_binary_model_0,
                {
                    (False, False): [DontCare],
                    (False, True): [DontCare],
                    (True, False): [True],
                    (True, True): [False],
                },
            ),
            (
                f_binary_model_1,
                {
                    (False, False): [DontCare, False],
                    (False, True): [DontCare, True],
                    (True, False): [True, DontCare],
                    (True, True): [False, DontCare],
                },
            ),
        ],
    )
    def test_check(self, model, expected_answers):
        py_model = PyFunctionModel(model)
        assert py_model.check([False, False]) == expected_answers[(False, False)]
        assert py_model.check([False, True]) == expected_answers[(False, True)]
        assert py_model.check([True, False]) == expected_answers[(True, False)]
        assert py_model.check([True, True]) == expected_answers[(True, True)]

    @pytest.mark.parametrize(
        "model, expected_tt",
        [
            (
                f_binary_model_0,
                [[DontCare, DontCare, True, False]],
            ),
            (
                f_binary_model_1,
                [
                    [DontCare, DontCare, True, False],
                    [False, True, DontCare, DontCare],
                ],
            ),
        ],
    )
    def test_get_model_tt(self, model, expected_tt):
        py_model = PyFunctionModel(model)
        assert py_model.get_model_truth_table() == expected_tt

    @pytest.mark.parametrize(
        "model, definition, expected_tt",
        [
            (
                f_binary_model_0,
                {
                    ((False, False), 0): True,
                    ((False, True), 0): False,
                },
                [[True, False, True, False]],
            ),
            (
                f_binary_model_1,
                {
                    ((False, False), 0): True,
                    ((False, True), 0): False,
                    ((True, False), 1): True,
                    ((True, True), 1): True,
                },
                [
                    [True, False, True, False],
                    [False, True, True, True],
                ],
            ),
        ],
    )
    def test_define(self, model, definition, expected_tt):
        py_model = PyFunctionModel(model)
        py_func = py_model.define(definition=definition)
        assert py_func.get_truth_table() == expected_tt


class TestPyFunction:

    @pytest.mark.parametrize(
        "function, input_size, output_size",
        [
            (f_max, 3, 1),
            (f_max_and_min, 4, 2),
            (f_sum, 3, 2),
        ],
    )
    def test_sizes(self, function: FunctionType, input_size: int, output_size: int):
        bf = PyFunction(function)
        assert bf.input_size == input_size
        assert bf.output_size == output_size

    @pytest.mark.parametrize(
        "inputs, value",
        [
            ([False, False, False], [False, False]),
            ([False, False, True], [False, True]),
            ([False, True, False], [False, True]),
            ([False, True, True], [True, False]),
            ([True, False, False], [False, True]),
            ([True, False, True], [True, False]),
            ([True, True, False], [True, False]),
            ([True, True, True], [True, True]),
        ],
    )
    def test_evaluate(self, inputs: list[bool], value: list[bool]):
        bf = PyFunction(f_sum)
        assert bf.evaluate(inputs) == value

    @pytest.mark.parametrize(
        "inputs, index, value",
        [
            ([False, False, False], 0, False),
            ([False, False, True], 1, True),
            ([False, True, False], 0, False),
            ([False, True, True], 1, False),
            ([True, False, False], 0, False),
            ([True, False, True], 1, False),
            ([True, True, False], 0, True),
            ([True, True, True], 1, True),
        ],
    )
    def test_evaluate_at(self, inputs: list[bool], index: int, value: bool):
        bf = PyFunction(f_sum)
        assert bf.evaluate_at(inputs, index) == value

    @pytest.mark.parametrize(
        "function, is_constant",
        [
            (f_const, True),
            (f_max, False),
        ],
    )
    def test_is_constant(self, function: FunctionType, is_constant: bool):
        bf = PyFunction(function)
        assert bf.is_constant() == is_constant

    @pytest.mark.parametrize(
        "function, output_index, inverse, is_monotone",
        [
            (f_const, 0, False, True),
            (f_max, 0, False, True),
            (f_max_and_min, 0, False, True),
            (f_max_and_min, 1, False, True),
            (f_max_and_min, 1, True, False),
        ],
    )
    def test_is_monotone(
        self,
        function: FunctionType,
        output_index: int,
        inverse: bool,
        is_monotone: bool,
    ):
        bf = PyFunction(function)
        assert bf.is_monotone_at(output_index, inverse=inverse) == is_monotone

    @pytest.mark.parametrize(
        "function, is_symmetric",
        [
            (f_max, True),
            (f_sum, True),
            (f_one_plus_minus, False),
        ],
    )
    def test_is_symmetric(self, function: FunctionType, is_symmetric: bool):
        bf = PyFunction(function)
        assert bf.is_symmetric() == is_symmetric

    @pytest.mark.parametrize(
        "negations",
        [
            [False, False, False],
            [False, False, True],
            [False, True, False],
            [False, True, True],
            [True, False, False],
            [True, False, True],
            [True, True, False],
            [True, True, True],
        ],
    )
    def test_find_negations_to_make_symmetric(self, negations: list[bool]):
        def f_sum_neg(arg1: bool, arg2: bool, arg3: bool) -> tp.Sequence[bool]:
            return sum_inputs_with_negations([arg1, arg2, arg3], negations)

        bf = PyFunction(f_sum_neg)
        negs = bf.find_negations_to_make_symmetric([0, 1])
        assert negs == negations or negs == [not b for b in negations]

    @pytest.mark.parametrize(
        "function, input_index, depends",
        [
            (f_arg0_and_arg1, 0, True),
            (f_arg0_and_arg1, 1, True),
            (f_arg0_and_arg1, 2, False),
            (f_arg1_or_arg2, 0, False),
            (f_arg1_or_arg2, 1, True),
            (f_arg1_or_arg2, 2, True),
            (f_arg0_xor_arg2, 0, True),
            (f_arg0_xor_arg2, 1, False),
            (f_arg0_xor_arg2, 2, True),
            (f_sum, 0, True),
            (f_sum, 1, True),
            (f_sum, 2, True),
        ],
    )
    def test_is_dependent_on_input_at(
        self,
        function: FunctionType,
        input_index: int,
        depends: bool,
    ):
        bf = PyFunction(function)
        assert bf.is_dependent_on_input_at(0, input_index) == depends

    @pytest.mark.parametrize(
        "function, input_index, is_equal",
        [
            (f_arg0, 0, True),
            (f_arg0, 1, False),
            (f_arg0, 2, False),
            (f_not_arg0, 0, False),
        ],
    )
    def test_is_output_equal_to_input(
        self,
        function: FunctionType,
        input_index: int,
        is_equal: bool,
    ):
        bf = PyFunction(function)
        assert bf.is_output_equal_to_input(0, input_index) == is_equal

    @pytest.mark.parametrize(
        "function, input_index, is_equal",
        [
            (f_not_arg0, 0, True),
            (f_not_arg0, 1, False),
            (f_not_arg0, 2, False),
            (f_arg0, 0, False),
        ],
    )
    def test_is_output_equal_to_input_negation(
        self,
        function: FunctionType,
        input_index: int,
        is_equal: bool,
    ):
        bf = PyFunction(function)
        assert bf.is_output_equal_to_input_negation(0, input_index) == is_equal

    @pytest.mark.parametrize(
        "function, significant_inputs",
        [
            (f_arg0_and_arg1, [0, 1]),
            (f_arg1_or_arg2, [1, 2]),
            (f_arg0_xor_arg2, [0, 2]),
            (f_arg0, [0]),
            (f_not_arg0, [0]),
            (f_const, []),
            (f_max, [0, 1, 2]),
            (f_sum, [0, 1, 2]),
        ],
    )
    def test_get_significant_inputs_of(
        self,
        function: FunctionType,
        significant_inputs: list[int],
    ):
        bf = PyFunction(function)
        assert bf.get_significant_inputs_of(0) == significant_inputs

    @pytest.mark.parametrize(
        "function, truth_table",
        [
            (lambda x, y: [x and y, x or y], [[0, 0, 0, 1], [0, 1, 1, 1]]),
            (lambda x, y: [x and y, x ^ y], [[0, 0, 0, 1], [0, 1, 1, 0]]),
        ],
    )
    def test_get_truth_table(
        self,
        function: FunctionType,
        truth_table: RawTruthTable,
    ):
        bf = PyFunction(function)
        assert bf.get_truth_table() == truth_table
