import inspect
import itertools
import typing as tp

from boolean_circuit_tool.core.boolean_function import BooleanFunction, RawTruthTable
from boolean_circuit_tool.core.circuit.utils import input_iterator_with_fixed_sum


__all__ = [
    'PythonFunction',
    'FunctionType',
]


FunctionType = tp.Callable[..., tp.Sequence[bool]]


class PythonFunction(BooleanFunction):
    """Boolean function given as a python function."""

    def __init__(self, func: FunctionType, *, output_size: tp.Optional[int] = None):
        """

        :param func: python callable. This callable will be invoked once
        on false input set if output_size is None.
        :param output_size: optional size of func output.

        """
        s = inspect.signature(func)
        self._func = func
        self._input_size = len(s.parameters)
        if output_size is None:
            result = func(*([0] * self.input_size))
            self._output_size = len(result)
        else:
            self._output_size = output_size

    @property
    def input_size(self) -> int:
        """
        :return: number of inputs.
        """
        return self._input_size

    @property
    def output_size(self) -> int:
        """
        :return: number of outputs.
        """
        return self._output_size

    def evaluate(self, inputs: tp.Sequence[bool]) -> tp.Sequence[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        return self._func(*inputs)

    def evaluate_at(self, inputs: tp.Sequence[bool], output_index: int) -> bool:
        """
        Get value of `output_index`th output that corresponds to provided `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        return self.evaluate(inputs)[output_index]

    def is_constant(self) -> bool:
        """
        Check if all outputs are constant (input independent).

        :return: True iff this function is constant.

        """
        input_iter = itertools.product((False, True), repeat=self.input_size)
        first_value = self.evaluate(next(input_iter))
        for x in input_iter:
            value = self.evaluate(x)
            if value != first_value:
                return False
        return True

    def is_constant_at(self, output_index: int) -> bool:
        """
        Check if output `output_index` is constant (input independent).

        :param output_index: index of desired output.
        :return: True iff output `output_index` is constant.

        """
        input_iter = itertools.product((False, True), repeat=self.input_size)
        first_value = self.evaluate_at(next(input_iter), output_index)
        for x in input_iter:
            value = self.evaluate_at(x, output_index)
            if value != first_value:
                return False
        return True

    def is_monotonic(self, *, inverse: bool) -> bool:
        """
        Check if all outputs are monotonic (output value doesn't decrease when
        inputs are enumerated in a classic order: 0000, 0001, 0010, 0011 ...).

        :param inverse: if True, will check that output values doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff this function is monotonic.

        """
        input_iter = itertools.product((False, True), repeat=self.input_size)
        old_value = self.evaluate(next(input_iter))
        for x in input_iter:
            value = self.evaluate(x)
            if not inverse and any(a < b for a, b in zip(value, old_value)):
                return False
            elif inverse and any(a > b for a, b in zip(value, old_value)):
                return False
        return True

    def is_monotonic_at(self, output_index: int, *, inverse: bool) -> bool:
        """
        Check if output `output_index` is monotonic (output value doesn't
        decrease when inputs are enumerated in a classic order: 0000, 0001,
        0010, 0011 ...).

        :param output_index: index of desired output.
        :param inverse: if True, will check that output value doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff output `output_index` is monotonic.

        """
        ones_started = False
        for x in itertools.product((False, True), repeat=self.input_size):
            value = self.evaluate_at(x, output_index)
            if not ones_started and (value != inverse):
                ones_started = True
            elif ones_started and (value == inverse):
                return False
        return True

    def is_symmetric(self) -> bool:
        """
        Check if all outputs are symmetric.

        :return: True iff this function is symmetric.

        """
        for number_of_true in range(self.input_size + 1):

            _iter = iter(input_iterator_with_fixed_sum(self.input_size, number_of_true))
            value: tp.Sequence[bool] = self.evaluate(next(_iter))

            for input_assignment in _iter:
                if value != self.evaluate(input_assignment):
                    return False

        return True

    def is_symmetric_at(self, output_index: int) -> bool:
        """
        Check that output `output_index` is symmetric.

        :param output_index: index of desired output.
        :return: True iff output `output_index` is symmetric.

        """
        for number_of_true in range(self.input_size + 1):

            _iter = iter(input_iterator_with_fixed_sum(self.input_size, number_of_true))
            value: bool = self.evaluate_at(next(_iter), output_index)

            for input_assignment in _iter:
                if value != self.evaluate_at(input_assignment, output_index):
                    return False

        return True

    def is_dependent_on_input_at(self, output_index: int, input_index: int) -> bool:
        """
        Check if output `output_index` depends on input `input_index` (there exist two
        input sets that differ only at `input_index`, but result in different value for
        `output_index`).

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` depends on input `input_index`.

        """
        for _x in itertools.product((False, True), repeat=self.input_size - 1):
            x = list(_x)
            x.insert(input_index, False)
            value1 = self.evaluate_at(x, output_index)
            x[input_index] = not x[input_index]
            value2 = self.evaluate_at(x, output_index)
            if value1 != value2:
                return True
        return False

    def is_output_equal_to_input(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` equals to input `input_index`.

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` equals to the input
        `input_index`.

        """
        for x in itertools.product((False, True), repeat=self.input_size):
            output_value = self.evaluate_at(x, output_index)
            input_value = x[input_index]
            if output_value != input_value:
                return False
        return True

    def is_output_equal_to_input_negation(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` equals to negation of input `input_index`.

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` equals to negation of input
        `input_index`.

        """
        for x in itertools.product((False, True), repeat=self.input_size):
            output_value = self.evaluate_at(x, output_index)
            input_value = not x[input_index]
            if output_value != input_value:
                return False
        return True

    def get_significant_inputs_of(self, output_index: int) -> list[int]:
        """
        Get indexes of all inputs on which output `output_index` depends on.

        :param output_index: index of desired output.
        :return: list of input indices.

        """
        return [
            input_index
            for input_index in range(self.input_size)
            if self.is_dependent_on_input_at(output_index, input_index)
        ]

    def find_negations_to_make_symmetric(
        self,
        output_index: list[int],
    ) -> tp.Optional[list[bool]]:
        """
        Check if exist input negations set such that function is symmetric on given
        output set.

        :param output_index: output index set
        :return: set of negations if it exists, else `None`.

        """

        def _filter_required_outputs(result: tp.Sequence[bool]):
            nonlocal output_index
            return [result[idx] for idx in output_index]

        for negations in itertools.product((False, True), repeat=self.input_size):
            symmetric = True
            for number_of_true in range(self.input_size + 1):

                _iter = iter(
                    input_iterator_with_fixed_sum(
                        self.input_size,
                        number_of_true,
                        negations=list(negations),
                    )
                )
                value: list[bool] = _filter_required_outputs(self.evaluate(next(_iter)))

                for input_assignment in _iter:
                    if value != _filter_required_outputs(
                        self.evaluate(input_assignment)
                    ):
                        symmetric = False
                        break

                if not symmetric:
                    break

            if symmetric:
                return list(negations)

        return None

    def get_truth_table(self) -> RawTruthTable:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, and `j`th column corresponds to the input which
        is a binary encoding of a number `j` (for example j=9 corresponds to [..., 1, 0,
        0, 1])

        :return: truth table describing this function.

        """
        table = [
            self.evaluate(x)
            for x in itertools.product((False, True), repeat=self.input_size)
        ]
        return [list(i) for i in zip(*table)]