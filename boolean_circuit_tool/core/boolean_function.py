import math
from typing import Callable
from itertools import product


class BooleanFunctionOut:

    def __init__(self, size: int, at: Callable[[list[int]], int]):
        self.size = size
        self.at = at

    def is_const(self) -> True:
        value_set = set()
        for x in product((0, 1), repeat=self.size):
            value = self.at(x)
            value_set.add(value)
            if len(value_set) > 1:
                return False
        return True


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
    def from_python_function(function: Callable[[list[int]], int], size: int) -> 'BooleanFunction':
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

    def __set_up_by_python_function(self, function: Callable[[list[int]], int], size: int):
        self.out_size = 1
        self.in_size = size

        self.outs = [BooleanFunctionOut(size, function)]

    def __set_up_by_bench(self, bench_path: str):
        raise NotImplementedError()
