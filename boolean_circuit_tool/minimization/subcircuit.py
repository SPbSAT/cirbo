import collections
import copy
import enum
import itertools
import logging
import typing as tp

import mockturtle_wrapper as mw

from boolean_circuit_tool.core.boolean_function import RawTruthTableModel
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Label
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.minimization.exception import (
    FailedValidationError,
    UnsupportedOperationError,
)
from boolean_circuit_tool.synthesis.circuit_search import Basis, CircuitFinderSat
from boolean_circuit_tool.synthesis.exception import NoSolutionError, SolverTimeOutError

Cut = tuple[Label, ...]

logger = logging.getLogger(__name__)

__all__ = ['minimize_subcircuits']


class NodeState(enum.Enum):
    UNCHANGED = 'UNCHANGED'
    MODIFIED = 'MODIFIED'
    REMOVED = 'REMOVED'


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
        truth_table: RawTruthTableModel = [list() for _ in range(len(output_patterns))]
        n = len(self.inputs)

        for i in itertools.product(('0', '1'), repeat=n):
            assignment: str = ''.join(i)
            for j, pattern in enumerate(output_patterns):
                output_patterns[j] >>= 1
                truth_table[j].append(
                    bool(pattern & 1) if assignment in self.inputs_tt else DontCare
                )

        return truth_table


def _read_cuts(
    cuts_raw: str, mapping: dict[Label, Label]
) -> tp.DefaultDict[Cut, set[Label]]:
    """
    Read mockturtle cuts into dictionary, where cut is a key and set of nodes for which
    it was selected as a value.

    :param cuts_raw: cuts found.
    :param mapping: mapping betwen node names in mockturtle klut_network and in names
        circuit.
    :return: found cuts.

    """
    cut_nodes: tp.DefaultDict[Cut, set[Label]] = collections.defaultdict(set)
    for line in cuts_raw.split('\n'):
        if line == '\n' or not line:
            continue
        data: list[str] = line.split()
        if data[0] == 'Node:':
            node: Label = mapping[data[1]]
        else:
            cut: Cut = tuple(mapping[x] for x in data[1:-1])
            cut_nodes[cut].add(node)
    return cut_nodes


def _powerset(iterable: tp.Iterable) -> itertools.chain:
    """
    Get all subsets from an iterable set.

    :param iterable: given set.
    :return: all subsets from set (including empty set).

    """
    lst = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(lst, x) for x in range(len(lst) + 1)
    )


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


def _is_cyclic(circuit: Circuit) -> bool:
    """
    Check whether circuit has oriented cycles (i.e. wrong circuit).

    :param circuit: circuit to check.
    :return: True if circuit has any oriented cycles, otherwise False.

    """
    sorted_gates: list[Label] = [node.label for node in circuit.top_sort(inverse=True)]
    gate_position: dict[Label, int] = {gate: i for i, gate in enumerate(sorted_gates)}
    for gate in sorted_gates:
        for operand in circuit.get_gate(gate).operands:
            if gate_position[gate] < gate_position[operand]:
                return True
    return False


def _get_subcircuits(
    circuit: Circuit, cuts: list[Cut], cut_nodes: tp.DefaultDict[Cut, set[Label]]
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
        Check whether `cut1` is nesten in `cut2`.

        :param cut1:
        :param cut2:
        :return: True if `cut1` is nested in `cut2, otherwise: False.

        """
        for gate in cut1:
            in_cut: bool = False
            for subcut in _powerset(cut2):
                if gate in cut_nodes[subcut]:
                    in_cut = True
                    break
            if not in_cut:
                return False
        return True

    good_cuts: list[Cut] = list()
    is_removed: dict[Cut, bool] = collections.defaultdict(bool)
    for i, cut in enumerate(cuts):
        for subcut in _powerset(cut):  # check whether cut should be removed
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

        for next_cut in cuts[i + 1 :]:
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
        for subcut in _powerset(cut):
            cut_nodes[cut].update(cut_nodes[subcut])

    node_pos: dict[Label, int] = {
        node.label: i for i, node in enumerate(circuit.top_sort(inverse=True))
    }
    subcircuits: list[_Subcircuit] = list()
    good_cuts = [cut for cut in good_cuts if len(cut) > 2]  # skip small cuts

    logger.debug(f"Process: {len(good_cuts)} cuts")

    outputs_set: set[Label] = set(circuit.outputs)
    inputs_tt: dict[int, list[int]] = {x: _generate_inputs_tt(x) for x in [3, 4, 5]}

    for cut in good_cuts:
        n: int = len(cut)
        inputs: set[Label] = set(cut)
        inputs_lst: list[Label] = list(inputs)
        outputs: list[Label] = list()
        nodes: list[Label] = sorted(list(cut_nodes[cut]), key=lambda x: node_pos[x])

        circuit_tt: tp.DefaultDict[Label, int] = collections.defaultdict(int)
        circuit_size: int = 0
        MAX_PATTERN: int = (1 << (1 << n)) - 1
        for i, node in enumerate(inputs_lst):
            circuit_tt[node] = inputs_tt[n][i]
        for node in nodes:
            if node in inputs:
                continue

            operands: tuple[Label, ...] = circuit.get_gate(node).operands
            users: list[Label] = circuit.get_gate_users(node)
            oper_type: str = circuit.get_gate(node).gate_type.name

            if oper_type == 'NOT':
                circuit_tt[node] = MAX_PATTERN - circuit_tt[operands[0]]
            elif oper_type == 'AND':
                circuit_tt[node] = circuit_tt[operands[0]] & circuit_tt[operands[1]]
            elif oper_type == 'NAND':
                circuit_tt[node] = MAX_PATTERN - (
                    circuit_tt[operands[0]] & circuit_tt[operands[1]]
                )
            elif oper_type == 'OR':
                circuit_tt[node] = circuit_tt[operands[0]] | circuit_tt[operands[1]]
            elif oper_type == 'NOR':
                circuit_tt[node] = MAX_PATTERN - (
                    circuit_tt[operands[0]] | circuit_tt[operands[1]]
                )
            elif oper_type == 'XOR':
                circuit_tt[node] = circuit_tt[operands[0]] ^ circuit_tt[operands[1]]
            elif oper_type == 'NXOR':
                circuit_tt[node] = MAX_PATTERN - (
                    circuit_tt[operands[0]] ^ circuit_tt[operands[1]]
                )
            else:
                raise UnsupportedOperationError()

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
        outputs.sort(key=lambda x: circuit_tt[x])
        subcircuits.append(
            _Subcircuit(
                inputs=list(inputs_lst)[::-1],
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


def minimize_subcircuits(
    circuit: Circuit,
    basis: Basis,
    *,
    enable_validation: bool = False,
    max_subcircuit_size: int = 9,
    solver_time_limit: int = 15,
    cut_size: int = 5,
    cut_limit: int = 25,
    fanout_size: int = 10000,
) -> Circuit:
    """
    Improve circuit's size by simplification its subcircuits using SAT-Solver.

    :param circuit: given circuit.
    :param basis: basis in which we want to simplify.
    :param enable_validation: if True checks that minimized circuit is equivalent to
        initial circuit.
    :param max_subcircuit_size: the maximum size of subcircuits for simplification.
        Important: simplification is based on SAT-Solver and can take a long time to
        work for sizes >=12.
    :param solver_time_limit: time limit in seconds for single subcicircuit minimization
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
    cuts_raw: str
    mapping: dict[Label, Label]
    cuts_raw, mapping = mw.enumerate_cuts(
        circuit.format_circuit(),
        cut_size,
        cut_limit,
        fanout_size,
    )
    cut_nodes: tp.DefaultDict[Cut, set[str]] = _read_cuts(cuts_raw, mapping)
    cuts: list[Cut] = sorted(cut_nodes.keys(), key=lambda x: len(x))

    logger.debug(f"Found {len(cuts)} cuts")

    initial_circuit: Circuit = copy.deepcopy(circuit)
    subcircuits: list[_Subcircuit] = _get_subcircuits(circuit, cuts, cut_nodes)
    subcircuits = _eval_dont_cares(circuit, subcircuits)
    node_states: dict[Label, NodeState] = {
        label: NodeState.UNCHANGED for label in circuit.gates
    }

    for iter, subcircuit in enumerate(subcircuits):
        inputs: list[Label] = subcircuit.inputs
        inputs_set: set[Label] = set(inputs)
        outputs_set: set[Label] = set(subcircuit.outputs)
        size: int = subcircuit.size

        if size > max_subcircuit_size:
            continue

        skip_subcircuit: bool = False
        for gate in subcircuit.gates:
            if node_states[gate] == NodeState.REMOVED or (
                node_states[gate] == NodeState.MODIFIED and gate not in inputs_set
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
                outputs_negation_mapping[output] = found_patterns[pattern]
            else:
                filtered_outputs.add(output)
                filtered_outputs_lst.append(output)
                found_patterns[pattern] = output

        outputs_tt: RawTruthTableModel = [
            row
            for i, row in enumerate(subcircuit.evaluate_truth_table_with_dont_cares())
            if subcircuit.outputs[i] in filtered_outputs
        ]
        try:
            new_subcircuit: Circuit = CircuitFinderSat(
                TruthTableModel(outputs_tt), size - 1, basis=basis
            ).find_circuit(time_limit=solver_time_limit)
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
        new_circuit.replace_subcircuit(
            new_subcircuit, input_labels_mapping, output_labels_mapping
        )

        if _is_cyclic(new_circuit):
            logger.debug("Circuit becomes cyclic")
            continue

        circuit = new_circuit
        logger.debug("Improved circuit size")

        # Update the states
        for output in filtered_outputs:
            node_states[output] = NodeState.MODIFIED

        for gate in subcircuit.gates:
            if gate in inputs_set or gate in outputs_set:
                continue
            node_states[gate] = NodeState.REMOVED

    if enable_validation:
        assignment: dict[Label, GateState] = {
            input: False for input in initial_circuit.inputs
        }
        for i in range(1 << len(initial_circuit.inputs)):
            if i:  # update assignment for new iteration
                idx: int = len(inputs) - 1
                while assignment[inputs[idx]]:
                    assignment[inputs[idx]] = False
                    idx -= 1
                assignment[inputs[idx]] = True
            if circuit.evaluate_circuit_outputs(
                assignment
            ) != initial_circuit.evaluate_circuit_outputs(assignment):
                raise FailedValidationError()

        logger.debug("Validation passed")

    return circuit
