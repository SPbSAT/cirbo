import itertools
import math
import typing as tp

from boolean_circuit_tool.core.boolean_function import BooleanFunction


__all__ = ['TruthTable']


def values_to_index(inputs: list[bool]) -> int:
    """
    Get index by input value set.

    :param inputs: input value set

    """
    return int(''.join(str(int(v)) for v in inputs), 2)


class TruthTable(BooleanFunction):
    def __init__(self, values: list[list[bool]]):
        self._values = [list(i) for i in zip(*values)]
        self._output_size = len(values)
        log = math.log2(len(values[0]))
        assert log.is_integer()
        self._input_size = int(log)

    def input_size(self) -> int:
        return self._input_size

    def output_size(self) -> int:
        return self._output_size

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        idx = values_to_index(inputs)
        return self.evaluate_at(idx)

    def evaluate_at(self, index: int) -> list[bool]:
        return self._values[index]

    def is_constant(self) -> bool:
        return all(self.is_constant_at(i) for i in range(self.output_size()))

    def is_constant_at(self, index: int) -> bool:
        value_set = set()
        for idx in range(2 ** self.input_size()):
            value = self.evaluate_at(idx)[index]
            value_set.add(value)
            if len(value_set) > 1:
                return False
        return True

    def is_monotonic(self, inverse: bool) -> bool:
        return all(self.is_monotonic_at(i, inverse) for i in range(self.output_size()))

    def is_monotonic_at(self, index: int, inverse: bool) -> bool:
        ones_started = False
        for idx in range(2 ** self.input_size()):
            value = self.evaluate_at(idx)[index]
            if not ones_started and (value != inverse):
                ones_started = True
            elif ones_started and (value == inverse):
                return False
        return True

    def is_dependent_from_input_of(self, output_index: int, input_index: int) -> bool:
        for x in itertools.product((0, 1), repeat=self.input_size() - 1):
            x = list(x)
            x.insert(input_index, 0)
            value1 = self.evaluate(x)[output_index]
            x[input_index] = not x[input_index]
            value2 = self.evaluate(x)[output_index]
            if value1 != value2:
                return True
        return False

    def get_out_as_input_negation(
        self, out_index: int, in_index: int
    ) -> tp.Optional[int]:
        for negation in (0, 1):
            eq = True
            for x in itertools.product((0, 1), repeat=self.input_size()):
                value = self.evaluate(list(x))[out_index]
                var = x[in_index]
                if value != (not var if negation else var):
                    eq = False
                    break
            if eq:
                return negation
        return None

    def get_significant_inputs_of(self, out_index) -> list[int]:
        result = []
        for i in range(self.input_size()):
            if self.is_dependent_from_input_of(out_index, i):
                result.append(i)
        return result

    def is_symmetric(self) -> bool:
        return (
            self.get_symmetric_and_negations_of(list(range(self.output_size())))
            is not None
        )

    def is_symmetric_at(self, out_index: int) -> bool:
        return self.get_symmetric_and_negations_of([out_index]) is not None

    def get_symmetric_and_negations_of(
        self, out_indexes: list[int]
    ) -> tp.Optional[list[bool]]:
        for negations in itertools.product((0, 1), repeat=self.input_size()):
            saved_values = [{} for _ in range(len(out_indexes))]
            symmetric = True
            for x in itertools.product((0, 1), repeat=self.input_size()):
                amount = sum(
                    x[i] * (1 if negations[i] else -1) for i in range(self.input_size())
                )
                values = self.evaluate(x)
                for index in out_indexes:
                    if amount not in saved_values[index]:
                        saved_values[index][amount] = values[index]
                    elif saved_values[index][amount] != values[index]:
                        symmetric = False
                        break
                if not symmetric:
                    break
            if symmetric:
                return [bool(v) for v in negations]
        return None

    def get_truth_table(self) -> 'TruthTable':
        return self
