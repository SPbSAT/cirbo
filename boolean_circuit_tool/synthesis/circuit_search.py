import datetime
import enum
import itertools
import logging
import multiprocessing as mp
import typing as tp

from concurrent.futures import TimeoutError

from pebble import concurrent

from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from boolean_circuit_tool.core.boolean_function import (
    BooleanFunctionModel,
    RawTruthTableModel,
)

from boolean_circuit_tool.core.circuit import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Circuit,
    Gate,
    GateType,
    GEQ,
    GT,
    INPUT,
    LEQ,
    LIFF,
    LNOT,
    LT,
    NAND,
    NOR,
    NXOR,
    OR,
    RIFF,
    RNOT,
    XOR,
)
from boolean_circuit_tool.core.logic import DontCare

from boolean_circuit_tool.sat import PySATSolverNames
from boolean_circuit_tool.synthesis.exception import (
    FixGateError,
    FixGateOrderError,
    ForbidWireOrderError,
    GateIsAbsentError,
    NoSolutionError,
    SolverTimeOutError,
    StringTruthTableError,
)

logger = logging.getLogger(__name__)

__all__ = [
    'Operation',
    'Basis',
    'PySATSolverNames',
    'CircuitFinderSat',
    'get_tt_by_str',
]


class Operation(enum.Enum):
    """Possible types of operator gate."""

    always_false_ = "0000"
    always_true_ = "1111"
    lnot_ = "1100"
    liff_ = "0011"
    rnot_ = "1010"
    riff_ = "0101"
    or_ = "0111"
    nor_ = "1000"
    and_ = "0001"
    nand_ = "1110"
    xor_ = "0110"
    nxor_ = "1001"
    gt_ = "0010"
    lt_ = "0100"
    geq_ = "1011"
    leq_ = "1101"


class Basis(enum.Enum):
    """Several types of bases."""

    AIG = [
        Operation.lnot_,
        Operation.and_,
        Operation.or_,
        Operation.nand_,
        Operation.nor_,
        Operation.gt_,
        Operation.lt_,
        Operation.geq_,
        Operation.leq_,
    ]
    XAIG = [
        Operation.lnot_,
        Operation.and_,
        Operation.or_,
        Operation.nand_,
        Operation.nor_,
        Operation.gt_,
        Operation.lt_,
        Operation.geq_,
        Operation.leq_,
        Operation.xor_,
        Operation.nxor_,
    ]
    FULL = [
        Operation.always_false_,
        Operation.always_true_,
        Operation.lnot_,
        Operation.rnot_,
        Operation.riff_,
        Operation.liff_,
        Operation.and_,
        Operation.or_,
        Operation.nand_,
        Operation.nor_,
        Operation.gt_,
        Operation.lt_,
        Operation.geq_,
        Operation.leq_,
        Operation.xor_,
        Operation.nxor_,
    ]


_tt_to_gate_type: tp.Dict[tp.Tuple, GateType] = {
    (0, 0, 0, 0): ALWAYS_FALSE,
    (0, 0, 0, 1): AND,
    (0, 0, 1, 0): GT,
    (0, 0, 1, 1): LIFF,
    (0, 1, 0, 0): LT,
    (0, 1, 0, 1): RIFF,
    (0, 1, 1, 0): XOR,
    (0, 1, 1, 1): OR,
    (1, 0, 0, 0): NOR,
    (1, 0, 0, 1): NXOR,
    (1, 0, 1, 0): RNOT,
    (1, 0, 1, 1): GEQ,
    (1, 1, 0, 0): LNOT,
    (1, 1, 0, 1): LEQ,
    (1, 1, 1, 0): NAND,
    (1, 1, 1, 1): ALWAYS_TRUE,
}


def _get_GateType_by_tt(gate_tt: tp.List[bool]) -> GateType:
    return _tt_to_gate_type[tuple(gate_tt)]


def get_tt_by_str(str_truth_table: tp.List[str]) -> RawTruthTableModel:
    """
    Convert a truth table from a list of strings to a list of TriValue lists.

    :param str_truth_table: List of strings representing the truth table
    :return: List of lists with TriValues corresponding to the input strings

    """

    def _char_to_trivalue(char):
        if char == "*":
            return DontCare
        if char == "1":
            return True
        if char == "0":
            return False
        raise StringTruthTableError()

    return [[_char_to_trivalue(char) for char in row] for row in str_truth_table]


class CircuitFinderSat:
    """
    A class for finding Boolean circuits using SAT-solvers.

    The CircuitFinder class encodes the problem of finding a Boolean circuit into a
    Conjunctive Normal Form (CNF) and uses a SAT-solver to find a solution.

    """

    def __init__(
        self,
        boolean_function_model: BooleanFunctionModel,
        number_of_gates: int,
        *,
        basis: tp.Union[Basis, tp.List[Operation]] = Basis.XAIG,
        need_normalized: bool = False,
    ):
        """
        Initializes the CircuitFinder instance.

        :param boolean_function_model:
        The function for which the circuit is needed.
        :param number_of_gates:
        The number of gates in the circuit we are finding.
        :param basis:
        The basis of gates in the circuit. Could be an arbitrary
        List of Operation or any of the default bases defined in Basis.
        Defaults to Basis.FULL.
        :param need_normalized: search for a normalization circuit, i.e.
        the circuit in which all gates satisfy the following property:
        g(0, 0) = 0.

        """

        self._boolean_function = boolean_function_model
        self._output_truth_tables = boolean_function_model.get_model_truth_table()
        self._basis_list = basis.value if isinstance(basis, Basis) else basis
        self._forbidden_operations = list(set(Basis.FULL.value) - set(self._basis_list))

        self._input_gates = list(range(boolean_function_model.input_size))
        self._internal_gates = list(
            range(
                boolean_function_model.input_size,
                boolean_function_model.input_size + number_of_gates,
            )
        )
        self._gates = list(range(boolean_function_model.input_size + number_of_gates))
        self._outputs = list(range(boolean_function_model.output_size))
        self.need_normalized = need_normalized
        self._vpool = IDPool()
        self._cnf = CNF()
        self._init_default_cnf_formula()

    def get_cnf(self) -> tp.List[tp.List[int]]:
        """
        Returns the list of clauses in Conjunctive Normal Form (CNF) representing the
        encoding of the circuit.

        :return: List of CNF clauses where each clause is a list of integers
            representing literals.

        """
        return self._cnf.clauses

    def find_circuit(
        self,
        solver_name: tp.Union[PySATSolverNames, str] = PySATSolverNames.CADICAL195,
        time_limit: tp.Union[int, None] = None,
    ) -> Circuit:
        """
        Solves the Conjunctive Normal Form (CNF) using a specified SAT-solver and
        returns the circuit if it exists.

        :param solver_name: The name of the SAT-solver to use. Default is
            PySATSolverNames.CADICAL195 ("cadical195").
        :param time_limit : Maximum time in seconds allowed for solving (default is
            None, meaning no time limit).
        :return: Circuit: If a solution is found within the specified time limit (if
            provided), returns the found circuit. If no solution is found or the solver
            times out, the corresponding error is raised.
        :raises NoSolutionError: If no solution is found for the CNF.
        :raises SolverTimeOutError: If the solver exceeds the specified time limit.

        """
        solver_name = PySATSolverNames(solver_name)
        logger.debug(
            f"Solving a CNF formula, "
            f"solver: {solver_name.value}, "
            f"time_limit: {time_limit}, "
            f"current time: {datetime.datetime.now()}"
        )
        if [] in self._cnf.clauses:
            raise NoSolutionError()

        logger.debug(f"Running {solver_name.value}")
        s = Solver(name=solver_name.value, bootstrap_with=self._cnf.clauses)
        if time_limit:

            @concurrent.process(timeout=time_limit, context=mp.get_context('fork'))
            def cnf_from_bench_wrapper():
                s.solve()
                return s.get_model()

            try:
                future = cnf_from_bench_wrapper()
                model = future.result()
            except TimeoutError as te:
                logger.debug("Solver timed out and is being stopped.")
                s.delete()
                raise SolverTimeOutError() from te
        else:
            s.solve()
            model = s.get_model()
            s.delete()

        if model is None:
            raise NoSolutionError()

        return self._get_circuit_by_model(model)

    def fix_gate(
        self,
        gate: int,
        first_predecessor: tp.Union[int, None] = None,
        second_predecessor: tp.Union[int, None] = None,
        gate_type: tp.Union[GateType, None] = None,
    ):
        """
        Fix a specific gate in the circuit.

        At least one predecessor should be given.
        :param gate: The gate to be fixed.
        :param first_predecessor: The first predecessor of the gate.
        :param second_predecessor: The second predecessor of the gate.
        :param gate_type: The gate type to be fixed.

        """

        if gate not in self._internal_gates:
            raise GateIsAbsentError()

        if first_predecessor is not None and first_predecessor not in self._gates:
            raise GateIsAbsentError()

        if second_predecessor is not None and second_predecessor not in self._gates:
            raise GateIsAbsentError()

        if first_predecessor is None and second_predecessor is None:
            raise FixGateError()

        if first_predecessor is not None and second_predecessor is not None:
            if not (gate > second_predecessor > first_predecessor):
                raise FixGateOrderError()
            self._cnf.append(
                [
                    self._predecessors_variable(
                        gate, first_predecessor, second_predecessor
                    )
                ]
            )
        elif first_predecessor is not None:
            if not (gate > first_predecessor):
                raise FixGateOrderError()
            for a, b in itertools.combinations(range(gate), 2):
                if a != first_predecessor and b != first_predecessor:
                    self._cnf.append([-self._predecessors_variable(gate, a, b)])

        # TODO: maintain gate_type
        # if gate_type:
        #     for a, b in itertools.product(range(2), repeat=2):
        #         bit = int(gate_type[2 * a + b])
        #         assert bit in range(2)
        #         self._cnf.append([(1 if bit else -1) * self._gate_type_variable(gate, a, b)])

    def forbid_wire(self, from_gate: int, to_gate: int):
        """
        Forbids the wire of a circuit from one gate to another.

        :param from_gate: The gate to be forbidden.
        :param to_gate: The gate to be forbidden.

        """
        if from_gate not in self._gates:
            raise GateIsAbsentError()
        if to_gate not in self._internal_gates:
            raise GateIsAbsentError()
        if from_gate >= to_gate:
            raise ForbidWireOrderError()

        for other in self._gates:
            if other >= to_gate:
                break
            if other == from_gate:
                continue
            self._cnf.append(
                [
                    -self._predecessors_variable(
                        to_gate, min(other, from_gate), max(other, from_gate)
                    )
                ]
            )

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
        for h in self._outputs:
            self._add_exactly_one_of(
                [self._output_gate_variable(h, gate) for gate in self._internal_gates]
            )

        # truth values for inputs
        for input_gate in self._input_gates:
            for t in range(1 << self._boolean_function.input_size):
                if self._is_dont_cares_input(t):
                    continue
                if (t >> (self._boolean_function.input_size - 1 - input_gate)) & 1:
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
                        self._cnf.append(
                            [
                                -self._predecessors_variable(
                                    gate, first_pred, second_pred
                                ),
                                (-1 if a else 1) * self._gate_value_variable(gate, t),
                                (-1 if b else 1)
                                * self._gate_value_variable(first_pred, t),
                                (-1 if c else 1)
                                * self._gate_value_variable(second_pred, t),
                                (1 if a else -1) * self._gate_type_variable(gate, b, c),
                            ]
                        )

        for h in self._outputs:
            for t in range(1 << self._boolean_function.input_size):
                if self._output_truth_tables[h][t] == DontCare:
                    continue
                for gate in self._internal_gates:
                    self._cnf.append(
                        [
                            -self._output_gate_variable(h, gate),
                            (1 if self._output_truth_tables[h][t] else -1)
                            * self._gate_value_variable(gate, t),
                        ]
                    )

        # each gate computes an allowed operation
        for gate in self._internal_gates:
            for op in self._forbidden_operations:
                assert len(op.value) == 4 and all(int(b) in (0, 1) for b in op.value)
                clause = [
                    (-1 if int(op.value[i]) == 1 else 1)
                    * self._gate_type_variable(gate, i // 2, i % 2)
                    for i in range(4)
                ]
                self._cnf.append(clause)

        if self.need_normalized:
            for gate in self._internal_gates:
                self._cnf.append([-self._gate_type_variable(gate, 0, 0)])

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

        This is determined by verifying that all corresponding output bits are
        DontCares, indicating "don't care" conditions.

        :params t: The integer representing the input in binary form.
        :return: True if all corresponding output bits are '*', otherwise False.

        """
        output_col = (
            self._output_truth_tables[g][t]
            for g in range(self._boolean_function.output_size)
        )
        return all((o == DontCare for o in output_col))

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

        assert gate in self._internal_gates
        assert first_pred in self._gates and second_pred in self._gates
        assert first_pred < second_pred < gate
        return self._vpool.id(f's_{gate}_{first_pred}_{second_pred}')

    def _output_gate_variable(self, h: int, gate: int) -> int:
        """
        Returns the variable representing that the h-th output is computed at the gate.

        :param h: Index of the output.
        :param gate: Index of the gate.
        :return: Variable representing the computation of the h-th output at the gate.

        """
        assert h in self._outputs
        assert gate in self._gates
        return self._vpool.id(f'g_{h}_{gate}')

    def _gate_value_variable(self, gate: int, t: int) -> int:
        """
        Returns the variable representing the t-th bit of the truth table of the gate.

        :param gate: Index of the gate.
        :param t: Index of the truth table bit.
        :return: Variable representing the t-th bit of the truth table of the gate.

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
        :return: Variable representing the output of the gate on inputs (p, q).

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
            initial_circuit.add_gate(Gate(str(gate), INPUT))

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
            initial_circuit.add_gate(
                Gate(
                    's' + str(gate),
                    _get_GateType_by_tt(gate_tt),
                    (str(first_predecessor_str), str(second_predecessor_str)),
                )
            )

        for h in self._outputs:
            for gate in self._gates:
                if self._output_gate_variable(h, gate) in model:
                    initial_circuit.mark_as_output('s' + str(gate))

        return initial_circuit
