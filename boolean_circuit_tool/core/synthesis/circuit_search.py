from abc import ABC
from enum import Enum
from itertools import combinations, product
from threading import Timer
from typing import Iterable, List
from pysat.formula import IDPool, CNFPlus, CNF
from pysat.solvers import Solver


class BooleanFunction:
    def __init__(self):
        self.number_of_outputs = 2
        self.number_of_input_gates = 2

    def get_truth_table(self):
        return ["01*1", "00*1"]


class BooleanOperation(Enum):
    """ Possible types of operator gate. """
    NOT = "1100"
    OR = "0111"
    NOR = "1000"
    AND = "0001"
    NAND = "1110"
    XOR = "0110"
    NXOR = "1001"


class BooleanBasis(Enum):
    AIG = [
        BooleanOperation.NOT,
        BooleanOperation.AND,
        BooleanOperation.OR,
        BooleanOperation.NAND,
        BooleanOperation.NOR
    ]
    # XIAG is a full binary basis
    XAIG = [
        BooleanOperation.NOT,
        BooleanOperation.AND,
        BooleanOperation.OR,
        BooleanOperation.NAND,
        BooleanOperation.NOR,
        BooleanOperation.XOR,
        BooleanOperation.NXOR
    ]


class PySATSolverNames(Enum):
    """ Enum version of pysat.solvers.SolverNames. """
    CADICAL103 = 'cadical103'
    CADICAL153 = 'cadical153'
    CADICAL193 = 'cadical195'
    CRYPTOSAT = 'crypto'
    GLUECARD3 = 'gluecard3'
    GLUECARD4 = 'gluecard4'
    GLUCOSE3 = 'glucose3'
    GLUCOSE4 = 'glucose4'
    GLUCOSE42 = 'glucose42  '
    LINGELING = 'lingeling'
    MAPLECHRONO = 'maplechrono'
    MAPLECM = 'maplecm'
    MAPLESAT = 'maplesat'
    MERGESAT3 = 'mergesat3'
    MINICARD = 'minicard'
    MINISAT22 = 'minisat22'
    MINISATGH = 'minisat-gh'


class CircuitFinder:
    def __init__(self, boolean_function: BooleanFunction, number_of_gates: int,
                 basis: BooleanBasis = BooleanBasis.XAIG):
        self.boolean_function = boolean_function
        self.output_truth_tables = boolean_function.get_truth_table()
        self.forbidden_operations = list(set(BooleanBasis.XAIG.value) - set(basis.value))

        self.input_gates = list(range(boolean_function.number_of_input_gates))
        self.internal_gates = list(
            range(boolean_function.number_of_input_gates, boolean_function.number_of_input_gates + number_of_gates))
        self.gates = list(range(boolean_function.number_of_input_gates + number_of_gates))
        self.outputs = list(range(boolean_function.number_of_outputs))

        self.vpool = IDPool()
        self.cnf = CNF()
        self.init_default_cnf_formula()

    def init_default_cnf_formula(self) -> None:
        # gate operates on two gates predecessors
        for gate in self.internal_gates:
            self.add_exactly_one_of([self.predecessors_variable(gate, a, b) for (a, b) in combinations(range(gate), 2)])

        # each output is computed somewhere
        for h in range(len(self.outputs)):
            self.add_exactly_one_of([self.output_gate_variable(h, gate) for gate in self.internal_gates])

        # truth values for inputs
        for input_gate in self.input_gates:
            for t in range(1 << self.boolean_function.number_of_input_gates):
                if self.is_dont_cares_input(t):
                    continue
                if (t >> (self.boolean_function.number_of_input_gates - 1 - input_gate)) & 1:
                    self.cnf.append([self.gate_value_variable(input_gate, t)])
                else:
                    self.cnf.append([-self.gate_value_variable(input_gate, t)])

        # gate computes the right value
        for gate in self.internal_gates:
            for first_pred, second_pred in combinations(range(gate), 2):
                for a, b, c in product(range(2), repeat=3):
                    for t in range(1 << self.boolean_function.number_of_input_gates):
                        if self.is_dont_cares_input(t):
                            continue
                        self.cnf.extend([[
                            -self.predecessors_variable(gate, first_pred, second_pred),
                            (-1 if a else 1) * self.gate_value_variable(gate, t),
                            (-1 if b else 1) * self.gate_value_variable(first_pred, t),
                            (-1 if c else 1) * self.gate_value_variable(second_pred, t),
                            (1 if a else -1) * self.gate_type_variable(gate, b, c)
                        ]])

        for h in self.outputs:
            for t in range(1 << self.boolean_function.number_of_input_gates):
                if self.output_truth_tables[h][t] == '*':
                    continue
                for gate in self.internal_gates:
                    self.cnf.extend([[
                        -self.output_gate_variable(h, gate),
                        (1 if self.output_truth_tables[h][t] == '1' else -1) * self.gate_value_variable(gate, t)
                    ]])

        # each gate computes a non-degenerate function (0, 1, x, -x, y, -y)
        for gate in self.internal_gates:
            self.cnf.extend([[self.gate_type_variable(gate, 0, 0), self.gate_type_variable(gate, 0, 1),
                              self.gate_type_variable(gate, 1, 0), self.gate_type_variable(gate, 1, 1)]])
            self.cnf.extend([[-self.gate_type_variable(gate, 0, 0), -self.gate_type_variable(gate, 0, 1),
                              -self.gate_type_variable(gate, 1, 0), -self.gate_type_variable(gate, 1, 1)]])

            self.cnf.extend([[self.gate_type_variable(gate, 0, 0), self.gate_type_variable(gate, 0, 1),
                              -self.gate_type_variable(gate, 1, 0), -self.gate_type_variable(gate, 1, 1)]])
            self.cnf.extend([[-self.gate_type_variable(gate, 0, 0), -self.gate_type_variable(gate, 0, 1),
                              self.gate_type_variable(gate, 1, 0), self.gate_type_variable(gate, 1, 1)]])

            self.cnf.extend([[self.gate_type_variable(gate, 0, 0), -self.gate_type_variable(gate, 0, 1),
                              self.gate_type_variable(gate, 1, 0), -self.gate_type_variable(gate, 1, 1)]])
            self.cnf.extend([[-self.gate_type_variable(gate, 0, 0), self.gate_type_variable(gate, 0, 1),
                              -self.gate_type_variable(gate, 1, 0), self.gate_type_variable(gate, 1, 1)]])

        # each gate computes an allowed operation
        for gate in self.internal_gates:
            for op in self.forbidden_operations:
                assert len(op.value) == 4 and all(int(b) in (0, 1) for b in op.value)
                clause = []
                for i in range(4):
                    clause.append((-1 if int(op.value[i]) == 1 else 1) * self.gate_type_variable(gate, i // 2, i % 2))
                self.cnf.append(clause)

    def add_exactly_one_of(self, literals):
        # self.cnf.append([list(literals), 1], is_atmost=True)
        # self.cnf.append([[-a for a in literals], len(literals) - 1], is_atmost=True)
        self.cnf.append(list(literals))
        self.cnf.extend([[-a, -b] for (a, b) in combinations(literals, 2)])

    def predecessors_variable(self, gate: int, first_pred: int, second_pred: int) -> int:
        # gate operates on gates first_pred and second_pred
        assert gate in self.internal_gates
        assert first_pred in self.gates and second_pred in self.gates
        assert first_pred < second_pred < gate
        return self.vpool.id(f's_{gate}_{first_pred}_{second_pred}')

    def output_gate_variable(self, h: int, gate: int) -> int:
        # h-th output is computed at gate
        assert h in self.outputs
        assert gate in self.gates
        return self.vpool.id(f'g_{h}_{gate}')

    def gate_value_variable(self, gate, t):
        # t-th bit of the truth table of gate
        assert gate in self.gates
        assert 0 <= t < 1 << self.boolean_function.number_of_input_gates
        return self.vpool.id(f'x_{gate}_{t}')

    # output of gate on inputs (p, q)
    def gate_type_variable(self, gate, p, q):
        assert 0 <= p <= 1 and 0 <= q <= 1
        assert gate in self.gates
        return self.vpool.id(f'f_{gate}_{p}_{q}')

    def get_cnf(self) -> List[List[int]]:
        return self.cnf.clauses

    def solve_cnf(self,
                  solver_name: PySATSolverNames = PySATSolverNames.CADICAL193,
                  verbose: bool = 1,
                  time_limit: int = None):

        s = Solver(name=solver_name.value, bootstrap_with=self.cnf.clauses)
        if time_limit:
            def interrupt(s):
                s.interrupt()

            solver_timer = Timer(time_limit, interrupt, [s])
            solver_timer.start()
            s.solve_limited(expect_interrupt=True)
        else:
            s.solve()

        model = s.get_model()
        s.delete()

        return model

    def is_dont_cares_input(self, t):
        output_col = [self.output_truth_tables[g][t] for g in
                      range(self.boolean_function.number_of_outputs)]
        return output_col.count('*') == self.boolean_function.number_of_outputs


# circ = CircuitFinder(BooleanFunction(), 2, BooleanBasis.AIG)
# print(circ.solve_cnf())
# my_cnf = CNFPlus()
# my_cnf.append([[1], 1], is_atmost=True)
