import collections
import copy
import itertools
import json
import logging

import mockturtle_wrapper as mw

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import (
    Basis,
    CircuitFinderSat,
    get_tt_by_str,
)
from boolean_circuit_tool.synthesis.exception import NoSolutionError

logger = logging.getLogger(__name__)


class Subcircuit:
    def __init__(
        self,
        inputs=None,
        gates=None,
        outputs=None,
        size=0,
        inputs_tt=None,
        patterns=None,
    ):
        self.inputs = [] if inputs is None else inputs
        self.gates = [] if gates is None else gates  # gates are in topsort order
        self.outputs = [] if outputs is None else outputs
        self.size = size
        self.inputs_tt = [] if inputs_tt is None else inputs_tt
        self.patterns = collections.defaultdict(int) if patterns is None else patterns

    @property
    def key(self):
        return tuple(
            [len(self.inputs)]
            + sorted([self.patterns[output] for output in self.outputs])
        )

    def evaluate_truth_table_with_dont_cares(self):
        """
        Returns truth table with don't cares based on possible inputs assignments
        (stored in `inputs_tt` field)

        :return: truth table for outputs

        """
        inputs_tt = self.inputs_tt
        output_patterns = [self.patterns[gate] for gate in self.outputs]
        truth_table = ['' for i in range(len(output_patterns))]
        n = len(self.inputs)

        for i in itertools.product(('0', '1'), repeat=n):
            assignment = ''.join(i)
            assignment = assignment[::-1]  # todo: check if needed
            for j, pattern in enumerate(output_patterns):
                bit = str(pattern & 1)
                output_patterns[j] >>= 1
                truth_table[j] += bit if assignment in inputs_tt else '*'
        return truth_table

    def serialize(self):
        return {
            'inputs': self.inputs,
            'gates': self.gates,
            'outputs': self.outputs,
            'size': self.size,
            'inputs_tt': self.inputs_tt,
            'patterns': self.patterns,
        }

    @staticmethod
    def deserialize(subcircuit_json):
        inputs = subcircuit_json.get('inputs', [])
        gates = subcircuit_json.get('gates', [])
        outputs = subcircuit_json.get('outputs', [])
        size = subcircuit_json.get('size', 0)
        inputs_tt = subcircuit_json.get('inputs_tt', [])
        patterns_raw = subcircuit_json.get('patterns', collections.defaultdict(int))
        patterns = collections.defaultdict(int)
        for key, val in patterns_raw.items():
            patterns[key] = val

        return Subcircuit(
            inputs=inputs,
            gates=gates,
            outputs=outputs,
            size=size,
            inputs_tt=inputs_tt,
            patterns=patterns,
        )

    def deserialize_array_from_file(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return [Subcircuit.deserialize(raw_subcircuit) for raw_subcircuit in data]

    @staticmethod
    def dump_list_to_file(subcircuits, filename):
        subcircuits_raw = [subcircuit.serialize() for subcircuit in subcircuits]
        with open(filename, 'w') as f:
            json.dump(subcircuits_raw, f, indent=4)


def read_cuts(cuts_raw, mapping):
    cut_nodes = collections.defaultdict(set)
    for line in cuts_raw.split('\n'):
        if line == '\n' or not line:
            continue
        data = line.split()
        if data[0] == 'Node:':
            node = mapping[data[1]]
        else:
            cut = tuple(mapping[x] for x in data[1:-1])
            cut_nodes[cut].add(node)
    return cut_nodes


def powerset(iterable):
    lst = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(lst, x) for x in range(len(lst) + 1)
    )


def generate_inputs_tt(sizes: list[int]):
    inputs_tt = collections.defaultdict(list)
    for size in sizes:
        inputs_tt[size] = [0] * size
        for i in range(1 << size):
            for j in range(size):
                inputs_tt[size][j] += ((i >> j) & 1) << i
    return inputs_tt


def is_cyclic(circuit):
    sorted_gates = [node.label for node in circuit.top_sort(inversed=True)]
    gate_position = {gate: i for i, gate in enumerate(sorted_gates)}
    for gate in sorted_gates:
        for operand in circuit.get_element(gate).operands:
            if gate_position[gate] < gate_position[operand]:
                return True
    return False


def get_subcircuits(circuit, cuts, cut_nodes):
    """
    Get subcircuits for simplification. Function processes given cuts and gets the most
    probable subcircuits for simplification.

    :param circuit: given circuit.
    :param cuts: cuts for the circuit.
    :param cut_nodes: dict for mapping cut to set of its nodes
    :return: list with subcircuits from the given circuit.

    """

    def is_nested_cut(cut1, cut2) -> bool:
        """
        Check whether `cut1` is nesten in `cut2`

        :param cut1:
        :param cut2:
        :return: `True` if `cut1` is nested in `cut2, otherwise: `False`

        """
        for gate in cut1:
            in_cut = False
            for subcut in powerset(cut2):
                if gate in cut_nodes[subcut]:
                    in_cut = True
                    break
            if not in_cut:
                return False
        return True

    good_cuts: list[tuple[str]] = []
    is_removed: dict[tuple[str], bool] = collections.defaultdict(bool)
    for i, cut in enumerate(cuts):
        for subcut in powerset(cut):  # check whether cut should be removed
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

    logger.info(f"Removed {len(cuts) - len(good_cuts)} nested cuts")

    # Fill cuts with all its gates
    for cut in good_cuts:
        for subcut in powerset(cut):
            cut_nodes[cut].update(cut_nodes[subcut])

    node_pos = {node.label: i for i, node in enumerate(circuit.top_sort(inversed=True))}
    subcircuits = []
    good_cuts = [cut for cut in good_cuts if len(cut) > 2]  # skip small cuts

    logger.info(f"Process: {len(good_cuts)} cuts")

    outputs_set = set(circuit.outputs)
    inputs_tt = generate_inputs_tt([3, 4, 5])

    for cut in good_cuts:
        n = len(cut)
        inputs = set(cut)
        inputs_lst = list(inputs)
        outputs = []
        nodes = sorted(list(cut_nodes[cut]), key=lambda x: node_pos[x])

        circuit_tt = collections.defaultdict(int)
        circuit_size = 0
        MAX_PATTERN = (1 << (1 << n)) - 1
        for i, node in enumerate(inputs_lst):
            circuit_tt[node] = inputs_tt[n][i]
        for node in nodes:
            if node in inputs:
                continue

            operands = circuit.get_element(node).operands
            users = circuit.get_element_users(node)
            oper_type = circuit.get_element(node).gate_type.name

            if len(operands) == 1:
                assert operands[0] in circuit_tt, f'{cut} {node} {operands} {oper_type}'
                circuit_tt[node] = MAX_PATTERN - circuit_tt[operands[0]]
            else:
                assert (
                    operands[0] in circuit_tt and operands[1] in circuit_tt
                ), f'{cut} {node} {operands} {oper_type}'
                if oper_type == 'AND':
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
                    print('Error! Incorrect operation')
                    assert False
                circuit_size += 1
            is_output = node in outputs_set
            if not is_output:
                for user in users:
                    if user not in cut_nodes[cut]:
                        is_output = True
                        break
            if is_output:
                outputs.append(node)
        outputs.sort(key=lambda x: circuit_tt[x])
        subcircuits.append(
            Subcircuit(
                inputs=list(inputs_lst)[::-1],
                gates=nodes,
                outputs=outputs,
                size=circuit_size,
                patterns=circuit_tt,
            )
        )
    return subcircuits


def eval_dont_cares(circuit, subcircuits):
    inputs = circuit.inputs
    assignment = {input: False for input in inputs}
    truth_table = collections.defaultdict(list)

    for i in range(1 << len(inputs)):
        if i:  # update assignment for new iteration
            idx = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        for gate, value in circuit.evaluate_circuit(assignment).items():
            truth_table[gate].append(int(value))

    for subcircuit in subcircuits:
        possible_assignments = set()
        for i in range(1 << len(inputs)):
            curr_assignment = []
            for input in subcircuit.inputs:
                curr_assignment.append(str(truth_table[input][i]))
            possible_assignments.add(''.join(curr_assignment))
        subcircuit.inputs_tt = sorted(possible_assignments)
    return subcircuits


def minimize(circuit: Circuit, basis: Basis) -> Circuit:
    cuts_raw, mapping = mw.enumerate_cuts(
        circuit.format_circuit()
    )  # tuple with string cuts representation
    cut_nodes = read_cuts(cuts_raw, mapping)
    cuts = sorted(cut_nodes.keys(), key=lambda x: len(x))

    logger.info(f"Found {len(cuts)} cuts")

    initial_circuit = copy.deepcopy(circuit)
    subcircuits = get_subcircuits(circuit, cuts, cut_nodes)
    subcircuits = eval_dont_cares(circuit, subcircuits)
    gate_status: dict[str, str] = collections.defaultdict(str)

    for iter, subcircuit in enumerate(subcircuits):
        inputs = subcircuit.inputs
        inputs_set = set(inputs)
        outputs_set = set(subcircuit.outputs)
        size = subcircuit.size

        if size > 11:
            continue

        skip_subcircuit = False
        for gate in subcircuit.gates:
            if gate_status[gate] == 'removed':
                skip_subcircuit = True
                break
            if gate_status[gate] == 'modified' and gate not in inputs_set:
                skip_subcircuit = True
                break
        if skip_subcircuit:
            continue

        found_patterns = collections.defaultdict(int)
        for input in inputs:
            found_patterns[subcircuit.patterns[input]] = input

        MAX_PATTERN = (1 << (1 << len(inputs))) - 1
        filtered_outputs = set()
        filtered_outputs_lst = []
        outputs_mapping = collections.defaultdict(int)
        outputs_negation_mapping = collections.defaultdict(int)

        for output in subcircuit.outputs:
            pattern = subcircuit.patterns[output]
            if pattern in found_patterns:
                outputs_mapping[output] = found_patterns[pattern]
            elif MAX_PATTERN - pattern in found_patterns:
                outputs_negation_mapping[output] = found_patterns[pattern]
            else:
                filtered_outputs.add(output)
                filtered_outputs_lst.append(output)
                found_patterns[pattern] = output

        outputs_tt = [
            row
            for i, row in enumerate(subcircuit.evaluate_truth_table_with_dont_cares())
            if subcircuit.outputs[i] in filtered_outputs
        ]
        new_subcircuit = None
        try:
            new_subcircuit = CircuitFinderSat(
                TruthTableModel(get_tt_by_str(outputs_tt)), size - 1, basis=basis
            ).find_circuit()
        except NoSolutionError:
            continue

        input_labels_mapping = {}
        output_labels_mapping = {}

        for i, old_gate in enumerate(inputs):
            new_gate = new_subcircuit.inputs[i]
            input_labels_mapping[old_gate] = new_gate

        for i, old_gate in enumerate(filtered_outputs_lst):
            new_gate = new_subcircuit.outputs[i]
            output_labels_mapping[old_gate] = new_gate

        for output in subcircuit.outputs:
            if output not in filtered_outputs:
                negation_gate = outputs_negation_mapping[output]
                new_gate = output_labels_mapping[negation_gate]

                for user in new_subcircuit.get_element_users(new_gate):
                    if new_subcircuit.get_element(user).gate_type.name == 'NOT':
                        output_labels_mapping[output] = user
                        new_subcircuit.mark_as_output(user)
                        break

        # Changing initial circuit
        new_circuit = copy.deepcopy(circuit)
        new_circuit.replace_subcircuit(
            new_subcircuit, input_labels_mapping, output_labels_mapping
        )

        if is_cyclic(new_circuit):
            continue

        circuit = new_circuit
        logger.info("Improved circuit size")

        for output in filtered_outputs:
            gate_status[output] = 'modified'

        for gate in subcircuit.gates:
            if gate in inputs_set or gate in outputs_set:
                continue
            gate_status[gate] = 'removed'

    # Sanity check
    assignment = {input: False for input in initial_circuit.inputs}
    for i in range(1 << len(initial_circuit.inputs)):
        if i:  # update assignment for new iteration
            idx = len(inputs) - 1
            while assignment[inputs[idx]]:
                assignment[inputs[idx]] = False
                idx -= 1
            assignment[inputs[idx]] = True
        assert circuit.evaluate_circuit_outputs(
            assignment
        ) == initial_circuit.evaluate_circuit_outputs(
            assignment
        ), "Initial circuit and circuit after impovement differ"

    logger.info("Check passed")

    return circuit
