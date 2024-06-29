import itertools

from boolean_function import BooleanFunction


__all__ = ['TruthTable']


class TruthTable(BooleanFunction):
    def __init__(self, values: list[list[bool]]):
        self.__values = values
        self.__output_size = len(values)
        self.__input_size = len(values[0])

    def input_size(self) -> int:
        return self.__input_size

    def output_size(self) -> int:
        return self.__output_size

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        idx = int(''.join([str(int(v)) for v in inputs]), 2)
        return [self.__values[i][idx] for i in range(self.__output_size)]

    def is_out_constant(self, index: int) -> bool:
        value_set = set()
        for x in itertools.product((0, 1), repeat=self.input_size()):
            value = self.evaluate(list(x))[index]
            value_set.add(value)
            if len(value_set) > 1:
                return False
        return True

    def is_constant(self) -> bool:
        return all([self.is_out_constant(i) for i in range(self.output_size())])

    def is_out_monotonic(self, index: int) -> bool:
        ones_started = False
        for x in itertools.product((0, 1), repeat=self.input_size()):
            value = self.evaluate(list(x))[index]
            if not ones_started and value:
                ones_started = True
            elif ones_started and not value:
                return False
        return True

    def is_monotonic(self) -> bool:
        return all(self.is_out_monotonic(i) for i in range(self.output_size()))

    def is_out_dependent_from_input(self, output_index: int, input_index: int) -> bool:
        for x in itertools.product((0, 1), repeat=self.input_size()):
            value1 = self.evaluate(x)[output_index]
            x[input_index] = not x[input_index]
            value2 = self.evaluate(x)[output_index]
            if value1 != value2:
                return True
        return False

    def get_out_is_input_negation(
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

    def get_out_significant_inputs(self, out_index) -> list[int]:
        result = []
        for i in range(self.input_size()):
            if self.is_out_dependent_from_input(out_index, i):
                result.append(i)
        return result

    def is_out_symmetric(self, out_index: int) -> bool:
        return self.get_out_symmetric_and_negations(out_index) is not None

    def is_symmetric(self) -> bool:
        return all([self.is_out_symmetric(i) for i in range(self.output_size())])

    def get_out_symmetric_and_negations(
        self, out_index: int
    ) -> tp.Optional[list[bool]]:
        for negations in itertools.product((0, 1), repeat=self.input_size()):
            values = {}
            symmetric = True
            for x in itertools.product((0, 1), repeat=self.input_size()):
                amount = sum(
                    [
                        x[i] * (1 if negations[i] else -1)
                        for i in range(self.input_size())
                    ]
                )
                value = self.evaluate(x)[out_index]
                if amount not in values:
                    values[amount] = value
                elif values[amount] != values:
                    symmetric = False
                    break
            if symmetric:
                return negations
        return None
