import collections
import copy
import enum
import itertools
import logging
import typing as tp
import uuid

import mockturtle_wrapper as mw
import more_itertools

from cirbo.core.boolean_function import RawTruthTableModel
from cirbo.core.circuit import Circuit
from cirbo.core.circuit.exceptions import CircuitValidationError
from cirbo.core.circuit.gate import Label
from cirbo.core.circuit.operators import GateState, Undefined
from cirbo.core.circuit.validation import check_circuit_has_no_cycles
from cirbo.core.logic import DontCare
from cirbo.core.truth_table import TruthTableModel
from cirbo.minimization.exception import (
    FailedValidationError,
    UnsupportedOperationError,
)
from cirbo.sat.miter import build_miter
from cirbo.sat.sat import is_circuit_satisfiable
from cirbo.synthesis.circuit_search import Basis, CircuitFinderSat, resolve_basis
from cirbo.synthesis.exception import NoSolutionError, SolverTimeOutError

Cut = tuple[Label, ...]

logger = logging.getLogger(__name__)

__all__ = ['minimize_subcircuits']


class _NodeState(enum.Enum):
    UNCHANGED = 'UNCHANGED'
    MODIFIED = 'MODIFIED'
    REMOVED = 'REMOVED'


class _PatternOperations:
    """
    Structure to evaluate patterns for small subcircuits. Pattern is an integer
    representation of truth table row for a gate.

    Method `eval_pattern` is used to get gate's pattern by patterns of its operands.

    """

    def __init__(self, number_of_inputs: int):
        self.max_pattern: int = (1 << (1 << number_of_inputs)) - 1

    def eval_pattern(self, operands: list[int], oper_type: str) -> int:
        if oper_type == 'NOT':
            return self.max_pattern - operands[0]
        elif oper_type == 'AND':
            return operands[0] & operands[1]
        elif oper_type == 'NAND':
            return self.max_pattern - (operands[0] & operands[1])
        elif oper_type == 'OR':
            return operands[0] | operands[1]
        elif oper_type == 'NOR':
            return self.max_pattern - (operands[0] | operands[1])
        elif oper_type == 'XOR':
            return operands[0] ^ operands[1]
        elif oper_type == 'NXOR':
            return self.max_pattern - (operands[0] ^ operands[1])
        elif oper_type == 'GEQ':
            return operands[0] | (self.max_pattern - operands[1])
        elif oper_type == 'LT':
            return self.max_pattern - (operands[0] | (self.max_pattern - operands[1]))
        elif oper_type == 'LEQ':
            return (self.max_pattern - operands[0]) | operands[1]
        elif oper_type == 'GT':
            return self.max_pattern - ((self.max_pattern - operands[0]) | operands[1])
        else:
            raise UnsupportedOperationError()


class _Subcircuit:
    def __init__(
        self,
        inputs=None,
        gates=None,
        outputs=None,
        size=0,
        inputs_tt=None,
        patterns=None,
    ):
        self.inputs: list[Label] = list() if inputs is None else inputs
        self.gates: list[Label] = (
            list() if gates is None else gates
        )  # gates are in top_sort order
        self.outputs: list[Label] = list() if outputs is None else outputs
        self.size: int = size
        self.inputs_tt: list[str] = list() if inputs_tt is None else inputs_tt
        self.patterns: tp.DefaultDict[Label, int] = (
            collections.defaultdict(int) if patterns is None else patterns
        )

    def evaluate_truth_table_with_dont_cares(self) -> RawTruthTableModel:
        """
        Return truth table with don't cares based on possible inputs assignments (stored
        in `inputs_tt` field).

        :return: truth table for outputs.

        """
        output_patterns: list[int] = [self.patterns[gate] for gate in self.outputs]
        truth_table: RawTruthTableModel = [list() for _ in output_patterns]
        n = len(self.inputs)

        for i in itertools.product(('0', '1'), repeat=n):
            assignment: str = ''.join(i)
            for j, pattern in enumerate(output_patterns):
                output_patterns[j] >>= 1
                truth_table[j].append(
                    bool(pattern & 1) if assignment in self.inputs_tt else DontCare
                )

        return truth_table


def _generate_inputs_tt(size: int) -> list[int]:
    """
    Generate inputs patterns by number of inputs.

    :param size: number of inputs.
    :return: list with integer patterns.

    """
    inputs_tt: list[int] = [0] * size
    for i in range(1 << size):
        for j in range(size):
            inputs_tt[j] += ((i >> j) & 1) << i
    return inputs_tt


def _get_subcircuits(
    circuit: Circuit,
    cuts: list[Cut],
    cut_nodes: tp.DefaultDict[Cut, set[Label]],
    max_subcircuit_size: int,
    cut_size: int,
) -> list[_Subcircuit]:
    """
    Get subcircuits for simplification. Function processes given cuts and gets the most
    probable subcircuits for simplification.

    :param circuit: given circuit.
    :param cuts: cuts for the circuit.
    :param cut_nodes: dict for mapping cut to set of its nodes
    :return: list with subcircuits from the given circuit.

    """

    def is_nested_cut(cut1: Cut, cut2: Cut) -> bool:
        """
        Check whether `cut1` is nested in `cut2`. One cut is called nested in another
        cut if for each node from the first cut its arbitrary path to any input node
        passes through some node from the second cut.

        :param cut1:
        :param cut2:
        :return: True if `cut1` is nested in `cut2, otherwise: False.

        """
        for gate in cut1:
            in_cut: bool = False
            for subcut in more_itertools.powerset(cut2):
                if gate in cut_nodes[subcut]:
                    in_cut = True
                    break
            if not in_cut:
                return False
        return True

    cuts.sort(key=lambda x: len(x))
    good_cuts: list[Cut] = list()
    is_removed: dict[Cut, bool] = collections.defaultdict(bool)
    for i, cut in enumerate(cuts):
        for subcut in more_itertools.powerset(
            cut
        ):  # check whether cut should be removed
            if is_removed[subcut]:
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue
        for prev_cut in good_cuts:
            if is_nested_cut(cut, prev_cut):
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue

        for j in range(i + 1, len(cuts)):
            next_cut = cuts[j]
            if len(next_cut) > len(cut):
                break
            if is_nested_cut(cut, next_cut):
                is_removed[cut] = True
                break
        if is_removed[cut]:
            continue
        good_cuts.append(cut)

    logger.debug(f"Removed {len(cuts) - len(good_cuts)} nested cuts")

    # Fill cuts with all its gates
    for cut in good_cuts:
        for subcut in more_itertools.powerset(cut):
            cut_nodes[cut].update(cut_nodes[subcut])

    node_pos: dict[Label, int] = {
        node.label: i for i, node in enumerate(circuit.top_sort(inverse=True))
    }
    subcircuits: list[_Subcircuit] = list()
    good_cuts = [cut for cut in good_cuts if 1 < len(cut) <= max_subcircuit_size]

    logger.debug(f"Process: {len(good_cuts)} cuts")

    outputs_set: set[Label] = set(circuit.outputs)
    inputs_tt: dict[int, list[int]] = {
        x: _generate_inputs_tt(x) for x in range(cut_size + 1)
    }

    for cut in good_cuts:
        n: int = len(cut)
        inputs: set[Label] = set(cut)
        inputs_lst: list[Label] = list(inputs)
        outputs: list[Label] = list()
        nodes: list[Label] = sorted(list(cut_nodes[cut]), key=lambda x: node_pos[x])

        circuit_tt: tp.DefaultDict[Label, int] = collections.defaultdict(int)
        circuit_size: int = 0
        pattern_operations: _PatternOperations = _PatternOperations(n)
        for i, node in enumerate(inputs_lst):
            circuit_tt[node] = inputs_tt[n][i]
        for node in nodes:
            if node in inputs:
                continue

            operands: tuple[Label, ...] = circuit.get_gate(node).operands
            users: list[Label] = circuit.get_gate_users(node)
            oper_type: str = circuit.get_gate(node).gate_type.name
            circuit_tt[node] = pattern_operations.eval_pattern(
                [circuit_tt[operand] for operand in operands], oper_type
            )

            if oper_type != 'NOT':
                circuit_size += 1
            is_output: bool = node in outputs_set
            if not is_output:
                for user in users:
                    if user not in cut_nodes[cut]:
                        is_output = True
                        break
            if is_output:
                outputs.append(node)
        subcircuits.append(
            _Subcircuit(
                inputs=inputs_lst[::-1],
                gates=nodes,
                outputs=outputs,
                size=circuit_size,
                patterns=circuit_tt,
            )
        )
    return subcircuits


def _eval_dont_cares(
    circuit: Circuit, subcircuits: list[_Subcircuit]
) -> list[_Subcircuit]:
    """
    Evaluate subcircuits truth table with don't cares.

    :param circuit: given circuit.
    :param subcircuits: subcircuits for don't cares evaluation.
    :return: list with updated subcircuits.

    """
    inputs: list[Label] = circuit.inputs
    assignment: dict[Label, GateState] = {input: False for input in inputs}
    truth_table: dict[Label, list[int]] = collections.defaultdict(list)

    for i in range(1 << len(inputs)):
        if i:  # update assignment for new iteration
            idx: int = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        for gate, value in circuit.evaluate_circuit(assignment).items():
            if value != Undefined:
                truth_table[gate].append(int(tp.cast(bool, value)))

    for subcircuit in subcircuits:
        possible_assignments: set[str] = set()
        for i in range(1 << len(inputs)):
            curr_assignment: list[str] = list()
            for input in subcircuit.inputs:
                curr_assignment.append(str(truth_table[input][i]))
            possible_assignments.add(''.join(curr_assignment))
        subcircuit.inputs_tt = sorted(possible_assignments)
    return subcircuits


def _get_internal_gates(
    circuit: "Circuit",
    inputs: list[Label],
    outputs: list[Label],
) -> list[Label]:
    """
    Get gates between given inputs and outputs in the circuit.

    :param circuit: circuit.
    :param inputs: list with inputs.
    :param outputs: list with outputs.
    :return: list with gates from the circuit

    """
    internal_gates: list[Label] = []
    label_is_visited: dict[Label, bool] = collections.defaultdict(bool)
    for output_label in outputs:
        queue: tp.Deque[Label] = collections.deque()
        if not label_is_visited[output_label]:
            label_is_visited[output_label] = True
            queue.append(output_label)
        while queue:
            label = queue.popleft()
            if label not in inputs and label not in outputs:
                internal_gates.append(label)
            if label not in inputs:
                for operand in circuit.get_gate(label).operands:
                    if not label_is_visited[operand]:
                        label_is_visited[operand] = True
                        queue.append(operand)
    return internal_gates


def _rename_subcircuit_gates(
    circuit: "Circuit",
    subcircuit: "Circuit",
    inputs_mapping: dict[Label, Label],
    outputs_mapping: dict[Label, Label],
):
    """
    Rename subcircuit gates.

    :param circuit: circuit for finding new labels.
    :param subcircuit: subcircuit in which we will change the names.
    :param inputs_mapping: label to label mapping between circuit nodes and subcitcuit
        inputs. The nodes of the circuit will participate in the search for new labels,
        and this mapping will also be used in the future replacement of the subcircuit.
    :param outputs_mapping: label to label mapping between circuit nodes and subcitcuit
        outputs. The nodes of the circuit will participate in the search for new labels,
        and this mapping will also be used in the future replacement of the subcircuit.
    :return: modified subcircuit.

    """
    labels_to_remove: list[Label] = _get_internal_gates(
        circuit,
        list(inputs_mapping.keys()),
        list(outputs_mapping.keys()),
    )

    tmp_mapping: dict[Label, Label] = {}  # used to avoid duplicating labels for nodes
    subcircuit_gates: list[Label] = list(subcircuit.gates.keys())
    for i, label in enumerate(subcircuit_gates):
        new_label: Label = f"tmp_{i}" + uuid.uuid4().hex
        tmp_mapping[label] = new_label
        subcircuit.rename_gate(label, new_label)

    for label1, label2 in inputs_mapping.items():
        subcircuit.rename_gate(old_label=tmp_mapping[label2], new_label=label1)
        inputs_mapping[label1] = label1

    for label1, label2 in outputs_mapping.items():
        if label1 not in inputs_mapping:
            subcircuit.rename_gate(old_label=tmp_mapping[label2], new_label=label1)
            outputs_mapping[label1] = label1

    i = 0
    for node in subcircuit.top_sort(inverse=True):
        if node.label not in inputs_mapping and node.label not in outputs_mapping:
            subcircuit.rename_gate(node.label, labels_to_remove[i])
            i += 1

    return subcircuit


def minimize_subcircuits(
    circuit: Circuit,
    basis: tp.Union[str, Basis],
    *,
    enable_validation: bool = False,
    max_subcircuit_size: int = 9,
    solver_time_limit_sec: int = 15,
    cut_size: int = 5,
    cut_limit: int = 25,
    fanout_size: int = 10000,
) -> Circuit:
    """
    Improve circuit's size by simplification its subcircuits using SAT-Solver.
    The algorithm is following:
    1. Get all limited size cuts.
    2. Remove nested cuts and build subcircuits on the remaining.
    3. Evaluate truth tables for subcircuits with don't cares.
    4. Try to improve found subcircuits using SAT-Solver for finding lower size circuit.

    Note: this method prefers not to have equivalent gates in the circuit.
    It's better to detect and simplify them before applying this function.

    :param circuit: given circuit.
    :param basis: basis in which we want to simplify.
    :param enable_validation: if True checks that minimized circuit is equivalent to
        initial circuit.
    :param max_subcircuit_size: the maximum size of subcircuits for simplification.
        Important: simplification is based on SAT-Solver and can take a long time to
        work for sizes >=12.
    :param solver_time_limit_sec: time limit in seconds for single subcicircuit minimization
        using SAT-Solver.
    :param cut_size: [mockturtle params] Maximum number of leaves for a cut.
    :param cut_limit: [mockturtle params] Maximum number of cuts for a node.
    :param fanin_limit: [mockturtle params] Maximum number of fan-ins for a node.
    :return: simplified circuit.
    :raises UnsupportedOperationError: If circuit has unsupported operation for
        minimization algorithm.
    :raises FailedValidationError: If minimized circuit is not equivalent to initial
        circuit.

    """
    _basis = resolve_basis(basis)

    node_cuts: dict[Label, list[Cut]] = mw.enumerate_cuts(
        circuit.format_circuit(),
        cut_size,
        cut_limit,
        fanout_size,
    )
    cut_nodes: tp.DefaultDict[Cut, set[Label]] = collections.defaultdict(set)
    for node, cuts in node_cuts.items():
        for cut in cuts:
            cut_nodes[tuple(cut)].add(node)
    cuts = list(cut_nodes.keys())

    logger.debug(f"Found {len(cuts)} cuts")

    initial_circuit: Circuit = copy.deepcopy(circuit)
    subcircuits: list[_Subcircuit] = _get_subcircuits(
        circuit, cuts, cut_nodes, max_subcircuit_size, cut_size
    )
    subcircuits = _eval_dont_cares(circuit, subcircuits)
    node_states: dict[Label, _NodeState] = {
        label: _NodeState.UNCHANGED for label in circuit.gates
    }

    for iter, subcircuit in enumerate(subcircuits):
        inputs: list[Label] = subcircuit.inputs
        inputs_set: set[Label] = set(inputs)
        size: int = subcircuit.size

        if size > max_subcircuit_size:
            continue

        skip_subcircuit: bool = False
        for gate in subcircuit.gates:
            if node_states[gate] == _NodeState.REMOVED or (
                node_states[gate] == _NodeState.MODIFIED and gate not in inputs_set
            ):
                skip_subcircuit = True
                break
        if skip_subcircuit:
            continue

        found_patterns: tp.DefaultDict[int, Label] = collections.defaultdict(Label)
        for input in inputs:
            found_patterns[subcircuit.patterns[input]] = input

        MAX_PATTERN: int = (1 << (1 << len(inputs))) - 1
        filtered_outputs: set[Label] = set()
        filtered_outputs_lst: list[Label] = list()
        outputs_mapping: tp.DefaultDict[Label, Label] = collections.defaultdict(Label)
        outputs_negation_mapping: tp.DefaultDict[Label, Label] = (
            collections.defaultdict(Label)
        )

        for output in subcircuit.outputs:
            pattern: int = subcircuit.patterns[output]
            if pattern in found_patterns:
                outputs_mapping[output] = found_patterns[pattern]
            elif MAX_PATTERN - pattern in found_patterns:
                outputs_negation_mapping[output] = found_patterns[MAX_PATTERN - pattern]
            else:
                filtered_outputs.add(output)
                filtered_outputs_lst.append(output)
                found_patterns[pattern] = output

        if not filtered_outputs:
            logger.debug("All outputs have trivial input patterns")
            for output in subcircuit.outputs:
                new_output = (
                    outputs_mapping[output]
                    if output in outputs_mapping
                    else outputs_negation_mapping[output]
                )
                for user in circuit.get_gate_users(output):
                    new_operands = tuple(
                        new_output if operand == output else operand
                        for operand in circuit.get_gate(user).operands
                    )
                    circuit.get_gate(user)._operands = new_operands
                    circuit._gate_to_users[new_output].append(user)
                circuit._outputs = [
                    new_output if x == output else x for x in circuit._outputs
                ]
                circuit.remove_gate(output)
                node_states[output] = _NodeState.REMOVED
                node_states[new_output] = _NodeState.REMOVED
            continue

        outputs_tt: RawTruthTableModel = [
            row
            for i, row in enumerate(subcircuit.evaluate_truth_table_with_dont_cares())
            if subcircuit.outputs[i] in filtered_outputs
        ]
        try:
            new_subcircuit: Circuit = CircuitFinderSat(
                TruthTableModel(outputs_tt),
                size - 1,
                basis=_basis,
            ).find_circuit(time_limit=solver_time_limit_sec)
        except NoSolutionError:
            logger.debug("Smaller subcircuit not found")
            continue
        except SolverTimeOutError:
            logger.debug("Lower subcircuit search is out of time")
            continue

        input_labels_mapping: dict[Label, Label] = {}
        output_labels_mapping: dict[Label, Label] = {}

        for i, old_gate in enumerate(inputs):
            new_gate: Label = new_subcircuit.inputs[i]
            input_labels_mapping[old_gate] = new_gate

        for i, old_gate in enumerate(filtered_outputs_lst):
            new_gate = new_subcircuit.outputs[i]
            output_labels_mapping[old_gate] = new_gate

        for output in subcircuit.outputs:
            if output not in filtered_outputs:
                negation_gate: Label = outputs_negation_mapping[output]
                new_gate = output_labels_mapping[negation_gate]

                for user in new_subcircuit.get_gate_users(new_gate):
                    if new_subcircuit.get_gate(user).gate_type.name == 'NOT':
                        output_labels_mapping[output] = user
                        new_subcircuit.mark_as_output(user)
                        break

        # Changing initial circuit
        new_circuit: Circuit = copy.deepcopy(circuit)
        _rename_subcircuit_gates(
            new_circuit, new_subcircuit, input_labels_mapping, output_labels_mapping
        )
        new_circuit.replace_subcircuit(
            new_subcircuit, input_labels_mapping, output_labels_mapping
        )

        try:
            check_circuit_has_no_cycles(new_circuit)
        except CircuitValidationError:
            logger.debug("Circuit becomes cyclic")
            continue

        circuit = new_circuit
        logger.debug("Improved circuit size")

        # Update the states
        for output in output_labels_mapping:
            node_states[output] = _NodeState.REMOVED

        for gate in _get_internal_gates(
            circuit,
            list(input_labels_mapping.keys()),
            list(output_labels_mapping.keys()),
        ):
            node_states[gate] = _NodeState.REMOVED

    if enable_validation:
        miter_circuit = build_miter(circuit, initial_circuit)
        if is_circuit_satisfiable(miter_circuit).answer:
            raise FailedValidationError()
        logger.debug("Validation passed")

    return circuit
