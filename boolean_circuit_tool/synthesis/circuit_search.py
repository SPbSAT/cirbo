import logging
import datetime
import enum
import itertools
import threading
import typing as tp

from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from boolean_circuit_tool.core.boolean_function import BooleanFunction
from boolean_circuit_tool.core.circuit import Circuit, Gate, GateType

logger = logging.getLogger(__name__)

__all__ = ['Operation', 'Basis', 'PySATSolverNames', 'CircuitFinder']


# class Function:
#     """Temporary class."""
#
#     def __init__(self, tt):
#         self.number_of_outputs = len(tt)
#         self.number_of_input_gates = int(math.log2(len(tt[0])))
#         self.tt = tt
#
#     def get_truth_table(self):
#         return self.tt


class Operation(enum.Enum):
    """Possible types of operator gate."""

    ZERO = "0000"
    ONE = "1111"
    NOT = "1100"
    IFF = "0011"
    NOT2 = "1010"
    IFF2 = "0101"
    OR = "0111"
    NOR = "1000"
    AND = "0001"
    NAND = "1110"
    XOR = "0110"
    NXOR = "1001"
    GREATER = "0010"
    LESS = "0100"
    GREATERORE = "1011"
    LESSORE = "1101"


class Basis(enum.Enum):
    """Several types of bases."""

    AIG = [
        Operation.NOT,
        Operation.AND,
        Operation.OR,
        Operation.NAND,
        Operation.NOR,
        Operation.GREATER,
        Operation.LESS,
        Operation.GREATERORE,
        Operation.LESSORE,
    ]
    XAIG = [
        Operation.NOT,
        Operation.AND,
        Operation.OR,
        Operation.NAND,
        Operation.NOR,
        Operation.GREATER,
        Operation.LESS,
        Operation.GREATERORE,
        Operation.LESSORE,
        Operation.XOR,
        Operation.NXOR,
    ]
    FULL = [
        Operation.ZERO,
        Operation.ONE,
        Operation.NOT2,
        Operation.IFF2,
        Operation.IFF,
        Operation.NOT,
        Operation.AND,
        Operation.OR,
        Operation.NAND,
        Operation.NOR,
        Operation.GREATER,
        Operation.LESS,
        Operation.GREATERORE,
        Operation.LESSORE,
        Operation.XOR,
        Operation.NXOR,
    ]


class PySATSolverNames(enum.Enum):
    """Enum version of pysat.solvers.SolverNames."""

    CADICAL103 = 'cadical103'
    CADICAL153 = 'cadical153'
    CADICAL193 = 'cadical195'
    CRYPTOSAT = 'crypto'
    GLUECARD3 = 'gluecard3'
    GLUECARD4 = 'gluecard4'
    GLUCOSE3 = 'glucose3'
    GLUCOSE4 = 'glucose4'
    GLUCOSE42 = 'glucose42'
    LINGELING = 'lingeling'
    MAPLECHRONO = 'maplechrono'
    MAPLECM = 'maplecm'
    MAPLESAT = 'maplesat'
    MERGESAT3 = 'mergesat3'
    MINICARD = 'minicard'
    MINISAT22 = 'minisat22'
    MINISATGH = 'minisat-gh'


_tt_to_gate_type = {
    (0, 1, 1, 1): GateType.OR,
    (1, 0, 0, 0): GateType.NOR,
    (0, 0, 0, 1): GateType.AND,
    (1, 1, 1, 0): GateType.NAND,
    (0, 1, 1, 0): GateType.XOR,
    (1, 0, 0, 1): GateType.NXOR,
    (1, 1, 0, 0): GateType.NOT,
    (1, 0, 1, 0): GateType.NOT,
    (0, 0, 1, 0): GateType.G,
    (0, 1, 0, 0): GateType.L,
    (1, 0, 1, 1): GateType.GE,
    (1, 1, 0, 1): GateType.LE
}


def get_GateType_by_tt(gate_tt: tp.List[bool]) -> GateType:
    return _tt_to_gate_type[tuple(gate_tt)]


class CircuitFinder:
    """
    A class for finding Boolean circuits using SAT-solvers.

    The CircuitFinder class encodes the problem of finding a Boolean circuit
    into a Conjunctive Normal Form (CNF) and
    uses a SAT-solver to find a solution.
    """

    def __init__(
            self,
            boolean_function: BooleanFunction,
            number_of_gates: int,
            basis: tp.Union[Basis, tp.List[Operation]] = Basis.XAIG,
    ):
        """
        Initializes the CircuitFinder instance.

        :param boolean_function:
        The function for which the circuit is needed.
        :param number_of_gates:
        The number of gates in the circuit we are finding.
        :param basis:
        The basis of gates in the circuit. Could be an arbitrary
        List of Operation or any of the default bases defined in Basis.
        Defaults to Basis.FULL.

        """

        self._boolean_function = boolean_function
        self._output_truth_tables = boolean_function.get_truth_table()
        self._basis_list = basis.value if isinstance(basis, Basis) else basis
        self._forbidden_operations = list(set(Basis.FULL.value) - set(self._basis_list))

        self._input_gates = list(range(boolean_function.input_size))
        self._internal_gates = list(
            range(
                boolean_function.input_size,
                boolean_function.input_size + number_of_gates,
            )
        )
        self._gates = list(
            range(boolean_function.input_size + number_of_gates)
        )
        self._outputs = list(range(boolean_function.output_size))

        self._vpool = IDPool()
        self._cnf = CNF()
        self._init_default_cnf_formula()

    def get_cnf(self) -> tp.List[tp.List[int]]:
        """
        Returns the list of clauses in Conjunctive Normal Form (CNF) representing the
        encoding of the circuit.

        :return: List of CNF clauses where each
        clause is a list of integers representing literals.

        """
        return self._cnf.clauses

    def solve_cnf(
            self,
            solver_name: PySATSolverNames = PySATSolverNames.CADICAL193,
            verbose: bool = True,
            time_limit: tp.Union[int, None] = None,
    ) -> tp.Union[Circuit, bool]:
        """
        Solves the Conjunctive Normal Form (CNF) using a specified SAT-solver and
        returns the circuit if it exists.


        :param solver_name: The name of the SAT-solver
        to use (default is PySATSolverNames.CADICAL193).
        :param verbose: If True, prints solver information
        during solving (default is True).
        :param time_limit : Maximum time in seconds allowed
        for solving (default is None, meaning no time limit).

        :return: Circuit or False: If a solution is found within
        the time limit (if specified), returns the found circuit.
        If no solution is found or the solver times out, returns False.

        """
        if verbose:
            logger.info(
                f"Solving a CNF formula, "
                f"solver: {solver_name.value}, "
                f"time_limit: {time_limit}, "
                f"current time: {datetime.datetime.now()}"
            )
        if [] in self._cnf.clauses:
            return False

        if verbose:
            logger.info(f"Running {solver_name.value}")
        s = Solver(name=solver_name.value, bootstrap_with=self._cnf.clauses)
        if time_limit:

            def interrupt(s):
                s.interrupt()

            solver_timer = threading.Timer(time_limit, interrupt, [s])
            solver_timer.start()
            s.solve_limited(expect_interrupt=True)
        else:
            s.solve()

        model = s.get_model()
        s.delete()

        if model is None:
            return False

        return self._get_circuit_by_model(model)

    def _init_default_cnf_formula(self) -> None:
        """Creating a CNF formula for finding a fixed-size circuit."""

        # gate operates on two gates predecessors
        for gate in self._internal_gates:
            self._add_exactly_one_of(
                [
                    self._predecessors_variable(gate, a, b)
                    for (a, b) in itertools.combinations(range(gate), 2)
                ]
            )

        # each output is computed somewhere
        for h in range(len(self._outputs)):
            self._add_exactly_one_of(
                [self._output_gate_variable(h, gate) for gate in self._internal_gates]
            )

        # truth values for inputs
        for input_gate in self._input_gates:
            for t in range(1 << self._boolean_function.input_size):
                if self._is_dont_cares_input(t):
                    continue
                if (
                        t >> (self._boolean_function.input_size - 1 - input_gate)
                ) & 1:
                    self._cnf.append([self._gate_value_variable(input_gate, t)])
                else:
                    self._cnf.append([-self._gate_value_variable(input_gate, t)])

        # gate computes the right value
        for gate in self._internal_gates:
            for first_pred, second_pred in itertools.combinations(range(gate), 2):
                for a, b, c in itertools.product(range(2), repeat=3):
                    for t in range(1 << self._boolean_function.input_size):
                        if self._is_dont_cares_input(t):
                            continue
                        self._cnf.extend(
                            [
                                [
                                    -self._predecessors_variable(
                                        gate, first_pred, second_pred
                                    ),
                                    (-1 if a else 1)
                                    * self._gate_value_variable(gate, t),
                                    (-1 if b else 1)
                                    * self._gate_value_variable(first_pred, t),
                                    (-1 if c else 1)
                                    * self._gate_value_variable(second_pred, t),
                                    (1 if a else -1)
                                    * self._gate_type_variable(gate, b, c),
                                ]
                            ]
                        )

        for h in self._outputs:
            for t in range(1 << self._boolean_function.input_size):
                print(self._output_truth_tables[h][t])
                if self._output_truth_tables[h][t] == '*':
                    continue
                for gate in self._internal_gates:
                    self._cnf.extend(
                        [
                            [
                                -self._output_gate_variable(h, gate),
                                (1 if self._output_truth_tables[h][t] == '1' else -1)
                                * self._gate_value_variable(gate, t),
                            ]
                        ]
                    )

        # each gate computes an allowed operation
        for gate in self._internal_gates:
            for op in self._forbidden_operations:
                assert len(op.value) == 4 and all(int(b) in (0, 1) for b in op.value)
                clause = []
                for i in range(4):
                    clause.append(
                        (-1 if int(op.value[i]) == 1 else 1)
                        * self._gate_type_variable(gate, i // 2, i % 2)
                    )
                self._cnf.append(clause)

    def _add_exactly_one_of(self, literals: tp.List[int]):
        """
        Adds the clauses to the CNF encoding the constraint that exactly one of the
        given literals is true.

        :param literals: A list of literals.

        """
        self._cnf.append(literals)
        self._cnf.extend([[-a, -b] for (a, b) in itertools.combinations(literals, 2)])

    def _is_dont_cares_input(self, t: int):
        """
        Checks if the input corresponding to the binary representation of the number `t`
        has no influence on the outputs.

        This is determined by verifying that all corresponding
        output bits are '*', indicating "don't care" conditions.

        :params t: The integer representing the input in binary form.

        :return: True if all corresponding output bits are '*',
        otherwise False.

        """
        output_col = [
            self._output_truth_tables[g][t]
            for g in range(self._boolean_function.output_size)
        ]
        return output_col.count('*') == self._boolean_function.output_size

    def _predecessors_variable(
            self, gate: int, first_pred: int, second_pred: int
    ) -> int:
        """
        Returns the variable representing that 'gate' operates on gates 'first_pred' and
        'second_pred'.

        Args:
            gate (int): The gate index.
            first_pred (int): The index of the first predecessor gate.
            second_pred (int): The index of the second predecessor gate.

        Returns:
            int: Variable representing the relationship
            where 'gate' operates on 'first_pred' and 'second_pred'.

        """
        # TODO: delete all asserts, here and in the following methods.

        assert gate in self._internal_gates
        assert first_pred in self._gates and second_pred in self._gates
        assert first_pred < second_pred < gate
        return self._vpool.id(f's_{gate}_{first_pred}_{second_pred}')

    def _output_gate_variable(self, h: int, gate: int) -> int:
        """
        Returns the variable representing that the h-th output is computed at the gate.


        :param h: Index of the output.
        :param gate: Index of the gate.

        :return: Variable representing the computation of
        the h-th output at the gate.

        """
        assert h in self._outputs
        assert gate in self._gates
        return self._vpool.id(f'g_{h}_{gate}')

    def _gate_value_variable(self, gate: int, t: int) -> int:
        """
        Returns the variable representing the t-th bit of the truth table of the gate.

        :param gate: Index of the gate.
        :param t: Index of the truth table bit.

        :return: Variable representing the t-th bit
        of the truth table of the gate.
        """
        assert gate in self._gates
        assert 0 <= t < 1 << self._boolean_function.input_size
        return self._vpool.id(f'x_{gate}_{t}')

    def _gate_type_variable(self, gate: int, p: int, q: int) -> int:
        """
        Returns the variable representing the output of the gate on inputs (p, q).

        :param gate: Index of the gate.
        :param p: First input value (0 or 1).
        :param q: Second input value (0 or 1).

        :return:Variable representing the output
        of the gate on inputs (p, q).

        """
        assert 0 <= p <= 1 and 0 <= q <= 1
        assert gate in self._gates
        return self._vpool.id(f'f_{gate}_{p}_{q}')

    def _get_circuit_by_model(self, model: tp.List[int]) -> Circuit:
        """
        Create the Circuit by the truth assignment of cnf.

        :param model: List of integers

        :return: Circuit
        """

        initial_circuit = Circuit()
        for gate in self._input_gates:
            initial_circuit.add_gate(Gate(str(gate), GateType.INPUT))

        for gate in self._internal_gates:
            first_predecessor, second_predecessor = None, None
            for f, s in itertools.combinations(range(gate), 2):
                if self._predecessors_variable(gate, f, s) in model:
                    first_predecessor, second_predecessor = f, s
                else:
                    assert -self._predecessors_variable(gate, f, s) in model

            gate_tt = []
            for p, q in itertools.product(range(2), repeat=2):
                if self._gate_type_variable(gate, p, q) in model:
                    gate_tt.append(True)
                else:
                    assert -self._gate_type_variable(gate, p, q) in model
                    gate_tt.append(False)

            first_predecessor_str = (
                str(first_predecessor)
                if first_predecessor in self._input_gates
                else 's' + str(first_predecessor)
            )
            second_predecessor_str = (
                str(second_predecessor)
                if second_predecessor in self._input_gates
                else 's' + str(second_predecessor)
            )

            if gate_tt == [1, 1, 0, 0] or gate == [1, 0, 1, 0]:
                initial_circuit.add_gate(
                    Gate(
                        's' + str(gate),
                        get_GateType_by_tt(gate_tt),
                        (str(first_predecessor_str),),
                    )
                )
            else:
                initial_circuit.add_gate(
                    Gate(
                        's' + str(gate),
                        get_GateType_by_tt(gate_tt),
                        (str(first_predecessor_str), str(second_predecessor_str)),
                    )
                )

        for h in self._outputs:
            for gate in self._gates:
                if self._output_gate_variable(h, gate) in model:
                    initial_circuit.mark_as_output('s' + str(gate))

        return initial_circuit
