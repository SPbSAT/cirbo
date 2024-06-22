import math
from itertools import product
from typing import Callable


__all__ = ['BooleanFunctionOut', 'BooleanFunction']


class BooleanFunctionOut:

    def __init__(self, size: int, at: Callable[[list[int]], int]):
        self.size = size
        self.at = at

    def is_constant(self) -> bool:
        value_set = set()
        for x in product((0, 1), repeat=self.size):
            value = self.at(list(x))
            value_set.add(value)
            if len(value_set) > 1:
                return False
        return True

    def does_depend_on_input(self, index: int) -> bool:
        for x in product((0, 1), repeat=self.size):
            value1 = self.at(x)
            x[index] = not x[index]
            value2 = self.at(x)
            if value1 != value2:
                return True
        return False

    def get_significant_inputs(self) -> list[int]:
        result = []
        for i in range(self.size):
            if self.does_depend_on_input(i):
                result.append(i)
        return result

    def is_symmetric(self) -> bool:
        for negations in product((0, 1), repeat=self.size):
            values = {}
            symmetric = True
            for x in product((0, 1), repeat=self.size):
                amount = sum(
                    [x[i] * (1 if negations[i] else -1) for i in range(self.size)]
                )
                value = self.at(x)
                if amount not in values:
                    values[amount] = value
                elif values[amount] != values:
                    symmetric = False
                    break
            if symmetric:
                return True
        return False


class BooleanFunction:

    def __init__(self):
        self.out_size = 0
        self.in_size = 0
        self.outs = []

    @staticmethod
    def from_truth_table(truth_table: list[list[int]]) -> 'BooleanFunction':
        bf = BooleanFunction()
        bf.__set_up_by_truth_table(truth_table)
        return bf

    @staticmethod
    def from_python_function(
        function: Callable[[list[int]], int], size: int
    ) -> 'BooleanFunction':
        bf = BooleanFunction()
        bf.__set_up_by_python_function(function, size)
        return bf

    @staticmethod
    def from_bench(bench_path: str) -> 'BooleanFunction':
        bf = BooleanFunction()
        bf.__set_up_by_bench(bench_path)
        return bf

    def __set_up_by_truth_table(self, truth_table: list[list[int]]):
        self.out_size = len(truth_table)
        assert self.out_size > 0
        self.in_size = int(math.log(len(truth_table[0])))

        self.outs = []
        for i in range(self.out_size):

            def at(x: list[int]) -> int:
                idx = int(''.join(map(str, x)), 2)
                return truth_table[i][idx]

            self.outs.append(BooleanFunctionOut(self.in_size, at))

    def __set_up_by_python_function(
        self, function: Callable[[list[int]], int], size: int
    ):
        self.out_size = 1
        self.in_size = size

        self.outs = [BooleanFunctionOut(size, function)]

    def __set_up_by_bench(self, bench_path: str):
        raise NotImplementedError()
