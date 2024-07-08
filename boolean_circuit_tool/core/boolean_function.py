import typing as tp

__all__ = ['BooleanFunction']


@tp.runtime_checkable
class BooleanFunction(tp.Protocol):
    """Protocol for any object that behaves like boolean function, e.g. Circuit,
    TruthTable or PythonFunction."""

    def input_size(self) -> int: ...
    def output_size(self) -> int: ...
    def evaluate(self, inputs: list[bool]) -> list[bool]: ...
    def evaluate_at(self, index: int) -> list[bool]: ...
    def is_constant(self) -> bool: ...
    def is_constant_at(self, index: int) -> bool: ...
    def is_monotonic(self, inverse: bool) -> bool: ...
    def is_monotonic_at(self, index: int, inverse: bool) -> bool: ...

    def is_out_dependent_from_input(
        self, output_index: int, input_index: int
    ) -> bool: ...

    def get_out_is_input_negation(
        self, out_index: int, in_index: int
    ) -> tp.Optional[int]: ...
    def get_significant_inputs_of(self, out_index) -> list[int]: ...

    def get_symmetric_and_negations_of(
        self, out_indexes: list[int]
    ) -> tp.Optional[list[bool]]: ...
    def is_symmetric(self) -> bool: ...

    def is_symmetric_at(self, out_index: int) -> bool: ...
    def get_truth_table(self) -> 'BooleanFunction': ...
