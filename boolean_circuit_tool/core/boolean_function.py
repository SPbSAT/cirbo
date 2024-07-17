import abc
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.exceptions import BadDefinitionError


__all__ = [
    'BooleanFunctionModel',
    'BooleanFunction',
]

from boolean_circuit_tool.core.logic import TriValue


BooleanFunctionT = tp.TypeVar('BooleanFunctionT', covariant=True)


@tp.runtime_checkable
class BooleanFunctionModel(tp.Protocol[BooleanFunctionT]):
    """
    Protocol for any object that describes model of boolean function, meaning that it
    defines subset of rules which must be satisfied by searched boolean function.

    Outputs of model can be either `bool`, or `DontCare` object, which
    means that output value is not fixed yet, and should be defined.

    """

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

    def check(self, inputs: list[bool]) -> tp.Sequence[TriValue]:
        """
        Get model output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """

    def check_at(self, inputs: list[bool], output_index: int) -> TriValue:
        """
        Get model value of `output_index`th output that corresponds to provided
        `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """

    def get_model_truth_table(self) -> tp.Sequence[tp.Sequence[TriValue]]:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, which may contain bool or DontCare values, and
        `j`th column corresponds to the input which is a binary encoding of a number `j`
        (for example j=9 corresponds to [..., 1, 0, 0, 1])

        :return: truth table describing this model.

        """

    def define(
        self,
        definition: tp.Mapping[tuple[tuple[bool, ...], int], bool],
    ) -> BooleanFunctionT:
        """
        Defines this model by defining ambiguous output values.

        :param definition: mapping of pairs (input value set, output index) to
        output values, required to completely define this boolean function model.
        :return: new object of `BooleanFunctionT` type.

        """


@tp.runtime_checkable
class BooleanFunction(BooleanFunctionModel, tp.Protocol):
    """
    Protocol for any object that behaves like boolean function, e.g. Circuit, TruthTable
    or PythonFunction.

    Any `BooleanFunction` is also a completely defined `BooleanFunctionModel`.

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

    def get_truth_table(self) -> tp.Sequence[tp.Sequence[bool]]:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, and `j`th column corresponds to the input which
        is a binary encoding of a number `j` (for example j=9 corresponds to [..., 1, 0,
        0, 1])

        :return: truth table describing this function.

        """

    def check(self, inputs: list[bool]) -> tp.Sequence[TriValue]:
        """
        Get model output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        return self.evaluate(inputs=inputs)

    def check_at(self, inputs: list[bool], output_index: int) -> TriValue:
        """
        Get model value of `output_index`th output that corresponds to provided
        `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        return self.evaluate_at(inputs=inputs, output_index=output_index)

    def get_model_truth_table(self) -> tp.Sequence[tp.Sequence[TriValue]]:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, which may contain bool or DontCare values, and
        `j`th column corresponds to the input which is a binary encoding of a number `j`
        (for example j=9 corresponds to [..., 1, 0, 0, 1])

        :return: truth table describing this model.

        """
        return self.get_truth_table()

    def define(
        self, definition: tp.Mapping[tuple[tuple[bool, ...], int], bool]
    ) -> tp_ext.Self:
        """
        Defines this model by defining ambiguous output values.

        :param definition: mapping of pairs (input value set, output index) to
        output values, required to completely define this boolean function model.
        :return: new object of `BooleanFunctionT` type.

        """
        if definition:
            raise BadDefinitionError("Boolean function is already defined.")
        return self
