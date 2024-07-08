import typing as tp

__all__ = ['BooleanFunction']


@tp.runtime_checkable
class BooleanFunction(tp.Protocol):
    """Protocol for any object that behaves like boolean function, e.g. Circuit,
    TruthTable or PythonFunction."""

    def input_size(self) -> int:
        """Get input count."""

    def output_size(self) -> int:
        """Get output count."""

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        """
        Get value by input value set.

        :param inputs: input value set.

        """

    def evaluate_at(self, index: int) -> list[bool]:
        """
        Get value by index.

        :param index: index.

        """

    def is_constant(self) -> bool:
        """Check if all outs are constant True or False."""

    def is_constant_at(self, index: int) -> bool:
        """
        Check if out is constant.

        :param index: out index

        """

    def is_monotonic(self, inverse: bool) -> bool:
        """
        Check if all outs are monotonic.

        :param inverse: is monotonic inverse

        """

    def is_monotonic_at(self, index: int, inverse: bool) -> bool:
        """
        Check if out is monotonic.

        :param index: out index
        :param inverse: is monotonic inverse

        """

    def is_dependent_from_input_of(self, output_index: int, input_index: int) -> bool:
        """
        Check if out is dependent from input.

        :param output_index: out index
        :param input_index: input index

        """

    def get_out_as_input_negation(
        self, out_index: int, in_index: int
    ) -> tp.Optional[int]:
        """
        Check if out is input or its negation and return this negation.

        :param out_index: out index
        :param in_index: input index

        """

    def get_significant_inputs_of(self, out_index) -> list[int]:
        """
        Get all inputs which out depends on.

        :param out_index: out index

        """

    def get_symmetric_and_negations_of(
        self, out_indexes: list[int]
    ) -> tp.Optional[list[bool]]:
        """
        Check if function is symmetric on some out set and returns inputs negations.

        :param out_indexes: out index set

        """

    def is_symmetric(self) -> bool:
        """Check if all outs are symmetric."""

    def is_symmetric_at(self, out_index: int) -> bool:
        """
        Check if out is symmetric.

        :param out_index: out index

        """

    def get_truth_table(self) -> 'BooleanFunction':
        """Get truth table."""
