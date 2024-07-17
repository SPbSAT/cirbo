import abc
import typing as tp

__all__ = ['BooleanFunction']


@tp.runtime_checkable
class BooleanFunction(tp.Protocol):
    """Protocol for any object that behaves like boolean function, e.g. Circuit,
    TruthTable or PythonFunction."""

    @property
    @abc.abstractmethod
    def input_size(self) -> int:
        """
        :return: number of inputs.
        """

    @property
    @abc.abstractmethod
    def output_size(self) -> int:
        """
        :return: number of outputs.
        """

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """

    def evaluate_at(self, inputs: list[bool], output_index: int) -> bool:
        """
        Get value of `output_index`th output that corresponds to provided `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """

    def is_constant(self) -> bool:
        """
        Check if all outputs are constant (input independent).

        :return: True iff this function is constant.

        """

    def is_constant_at(self, output_index: int) -> bool:
        """
        Check if output `output_index` is constant (input independent).

        :param output_index: index of desired output.
        :return: True iff output `output_index` is constant.

        """

    def is_monotonic(self, *, inverse: bool) -> bool:
        """
        Check if all outputs are monotonic (output value doesn't decrease when
        inputs are enumerated in a classic order: 0000, 0001, 0010, 0011 ...).

        :param inverse: if True, will check that output values doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff this function is monotonic.

        """

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

    def is_symmetric(self) -> bool:
        """
        Check if all outputs are symmetric.

        :return: True iff this function.

        """

    def is_symmetric_at(self, output_index: int) -> bool:
        """
        Check that output `output_index` is symmetric.

        :param output_index: index of desired output.
        :return: True iff output `output_index` is symmetric.

        """

    def is_dependent_on_input_at(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` depends on input `input_index` (there exist two
        input sets that differ only at `input_index`, but result in different value for
        `output_index`).

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` depends on input `input_index`.

        """

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

    def get_significant_inputs_of(self, output_index: int) -> list[int]:
        """
        Get indexes of all inputs on which output `output_index` depends on.

        :param output_index: index of desired output.
        :return: list of input indices.

        """

    def get_symmetric_and_negations_of(
        self,
        output_index: list[int],
    ) -> tp.Optional[list[bool]]:
        """
        Check if function is symmetric on some output set and returns inputs negations.

        :param output_index: output index set

        """

    def get_truth_table(self) -> list[list[bool]]:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, and `j`th column corresponds to the input which
        is a binary encoding of a number `j` (for example j=9 corresponds to [..., 1, 0,
        0, 1])

        :return: truth table describing this function.

        """
