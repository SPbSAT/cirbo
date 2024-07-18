import copy
import itertools
import math
import typing as tp

from boolean_circuit_tool.core.boolean_function import (
    BooleanFunction,
    BooleanFunctionModel,
    RawTruthTable,
    RawTruthTableModel,
)

from boolean_circuit_tool.core.circuit.utils import input_iterator
from boolean_circuit_tool.core.logic import TriValue
from boolean_circuit_tool.core.utils import get_bit_value, input_to_canonical_index


__all__ = [
    'TruthTableModel',
    'TruthTable',
]


class TruthTableModel(BooleanFunctionModel):
    """Boolean function model given as a truth table with don't care outputs."""

    def __init__(self, table: RawTruthTableModel):
        """
        :param table: truth table given as a list of lists of bools. `i`th list
        is a truth table for output number `i`, trimmed to contain only output
        values. Element `j` of list `i` is value for output `i` for input which
        is a binary encoding of a number `j` (e.g. 9 -> [..., 1, 0, 0, 1]).

        """
        self._input_size = resolve_input_size(table)
        self._output_size = len(table)

        self._table: RawTruthTableModel = table
        # Transposed truth table, element (i, j) of which is a value
        # of the output `j` when evaluated at input number `i`.
        self._table_t: RawTruthTableModel = [list(i) for i in zip(*table)]

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

    def check(self, inputs: list[bool]) -> tp.Sequence[TriValue]:
        """
        Get model output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        idx = input_to_canonical_index(inputs)
        return self._table_t[idx]

    def check_at(self, inputs: list[bool], output_index: int) -> TriValue:
        """
        Get model value of `output_index`th output that corresponds to provided
        `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        idx = input_to_canonical_index(inputs)
        return self._table_t[idx][output_index]

    def get_model_truth_table(self) -> RawTruthTableModel:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, which may contain bool or DontCare values, and
        `j`th column corresponds to the input which is a binary encoding of a number `j`
        (for example j=9 corresponds to [..., 1, 0, 0, 1])

        :return: truth table describing this model.

        """
        return self._table

    def define(
        self,
        definition: tp.Mapping[tuple[tuple[bool, ...], int], bool],
    ) -> 'TruthTable':
        """
        Defines this model by defining ambiguous output values.

        :param definition: mapping of pairs (input value set, output index) to
        output values, required to completely define this boolean function model.
        :return: new object of `BooleanFunctionT` type.

        """
        _table_cp = copy.deepcopy(self._table)
        for (input_value, output_idx), output_value in definition.items():
            _table_cp[output_idx][input_to_canonical_index(input_value)] = output_value

        return TruthTable(
            table=tp.cast(RawTruthTable, _table_cp),
        )


class TruthTable(BooleanFunction):
    """Boolean function given as a truth table."""

    def __init__(self, table: RawTruthTable):
        """
        :param table: truth table given as a list of lists of bools. `i`th list
        is a truth table for output number `i`, trimmed to contain only output
        values. Element `j` of list `i` is value for output `i` for input which
        is a binary encoding of a number `j` (e.g. 9 -> [..., 1, 0, 0, 1]).

        """
        self._input_size = resolve_input_size(table)
        self._output_size = len(table)

        self._table: RawTruthTable = table
        # Transposed truth table, element (i, j) of which is a value
        # of the output `j` when evaluated at input number `i`.
        self._table_t: RawTruthTable = [list(i) for i in zip(*table)]

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

    def evaluate(self, inputs: list[bool]) -> tp.Sequence[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        idx = input_to_canonical_index(inputs)
        return self._table_t[idx]

    def evaluate_at(self, inputs: list[bool], output_index: int) -> bool:
        """
        Get value of `output_index`th output that corresponds to provided `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        idx = input_to_canonical_index(inputs)
        return self._table_t[idx][output_index]

    def is_constant(self) -> bool:
        """
        Check if all outputs are constant (input independent).

        :return: True iff this function is constant.

        """
        return all(self.is_constant_at(i) for i in range(self.output_size))

    def is_constant_at(self, output_index: int) -> bool:
        """
        Check if output `output_index` is constant (input independent).

        :param output_index: index of desired output.
        :return: True iff output `output_index` is constant.

        """

        first_value = self._table[output_index][0]
        for value in self._table[output_index]:
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

        return all(
            self.is_monotonic_at(i, inverse=inverse) for i in range(self.output_size)
        )

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
        for value in self._table[output_index]:
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

            _iter = iter(input_iterator(self.input_size, number_of_true))
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

            _iter = iter(input_iterator(self.input_size, number_of_true))
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
        for idx, output_value in enumerate(self._table[output_index]):
            input_value = get_bit_value(idx, input_index)
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
        for idx, output_value in enumerate(self._table[output_index]):
            input_value = not get_bit_value(idx, input_index)
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
                    input_iterator(
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
        return self._table


def resolve_input_size(table: tp.Union[RawTruthTableModel, RawTruthTable]) -> int:
    """
    Calculates number of inputs based on provided raw truth table.

    :param table: raw truth table.
    :return: number of inputs of function described by a truth table.

    """
    log = math.log2(len(table[0]))
    if not log.is_integer():
        raise ValueError(
            "Truth table got raw truth table with number "
            "of rows not equal to a power of two."
        )
    return int(log)
