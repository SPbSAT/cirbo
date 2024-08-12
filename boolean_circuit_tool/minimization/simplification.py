"""
Module contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

import collections
import itertools
import random

from boolean_circuit_tool.core.circuit import Circuit, GateState
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Gate,
    NAND,
    NOT,
    NXOR,
    OR,
    XOR,
)

__all__ = [
    'remove_leaves_and_double_not',
    'delete_equivalent_gates',
    'merge_same_successors',
    'remove_identities',
]


def remove_leaves_and_double_not(circuit: Circuit) -> Circuit:
    """
    Simplifies the circuit by removing leaves and consecutive NOT gates. Traverses the
    circuit recursively, starting from the output gates, and rebuilds the circuit
    without redundant NOT gates and unused gates.

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit

    """
    new_circuit = Circuit()
    visited = set()  # Stores the labels of already visited gates
    replace_map: dict[str, str] = {}  # Maps original gate labels to new gate labels

    def _dfs(gate_label):
        if gate_label in visited:
            return replace_map.get(gate_label)
        visited.add(gate_label)

        original_gate = circuit.get_gate(gate_label)
        operands = []

        if original_gate.gate_type == NOT:
            operand_label = original_gate.operands[0]
            operand_gate = circuit.get_gate(operand_label)
            if operand_gate.gate_type == NOT:
                result_label = _dfs(operand_gate.operands[0])
                replace_map[gate_label] = result_label
                return result_label
            else:
                operands.append(_dfs(operand_label))
        else:
            operands = [_dfs(op_label) for op_label in original_gate.operands]

        if gate_label not in replace_map:
            new_gate_label = gate_label
            new_gate = Gate(new_gate_label, original_gate.gate_type, tuple(operands))
            new_circuit.add_gate(new_gate)
            replace_map[gate_label] = new_gate_label

        return replace_map[gate_label]

    for output_label in circuit.outputs:
        output_gate_label = _dfs(output_label)
        new_circuit.mark_as_output(output_gate_label)

    return new_circuit


def _find_equivalent_gates(circuit: Circuit) -> list[list[str]]:
    """
    Identifies and groups equivalent gates within the circuit based on their full truth
    tables.

    :param circuit: - the circuit to analyze for equivalent gates
    :return: - a list of groups, each containing labels of equivalent gates

    """
    input_size = len(circuit.inputs)
    input_combinations = list(itertools.product([False, True], repeat=input_size))
    gate_truth_tables = collections.defaultdict(list)

    for inputs in input_combinations:
        assignment: dict[str, GateState] = {
            input_label: value for input_label, value in zip(circuit.inputs, inputs)
        }
        gate_values = circuit.evaluate_circuit(assignment)
        for gate_label, output in gate_values.items():
            gate_truth_tables[gate_label].append(output)

    truth_table_to_gates = collections.defaultdict(list)
    for gate_label, truth_table in gate_truth_tables.items():
        truth_key = tuple(truth_table)
        truth_table_to_gates[truth_key].append(gate_label)
    equivalent_groups = [
        gates for gates in truth_table_to_gates.values() if len(gates) > 1
    ]

    return equivalent_groups


def _replace_equivalent_gates(
    circuit: Circuit, equivalent_groups: list[list[str]]
) -> Circuit:
    """
    Reconstructs the circuit by replacing all equivalent gates identified by
    `find_equivalent_gates` with a single representative from each group, updating
    references accordingly.

    :param circuit: - the original circuit
    :param equivalent_groups: - groups of equivalent gates
    :return: - a new circuit with equivalent gates replaced

    """
    replacement_map = {}  # Maps original gate labels to new gate labels
    new_circuit = Circuit()

    for group in equivalent_groups:
        if len(group) > 1:
            keep = group[0]
            for gate_to_replace in group[1:]:
                replacement_map[gate_to_replace] = keep

    for gate_label, gate in circuit.gates.items():
        new_gate_label = replacement_map.get(gate_label, gate_label)
        new_operands = tuple(
            replacement_map.get(operand, operand) for operand in gate.operands
        )

        if new_gate_label not in new_circuit.gates:
            new_gate = Gate(new_gate_label, gate.gate_type, new_operands)
            new_circuit.add_gate(new_gate)

        if gate_label in circuit.outputs:
            if new_gate_label not in new_circuit.outputs:
                new_circuit.mark_as_output(new_gate_label)

    return new_circuit


def delete_equivalent_gates(circuit: Circuit) -> Circuit:
    """
    Finds groups of equivalent gates using the full truth table comparison and replaces
    them with a single gate, updating all the references to the old ones.

    Warning: the execution time grows exponentially as the number of inputs increases.
    For circuits with more than 20 inputs it is recommended to use merge_same_successors().

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit

    """
    equivalent_gate_groups = _find_equivalent_gates(circuit)
    return _replace_equivalent_gates(circuit, equivalent_gate_groups)


def merge_same_successors(circuit: Circuit, num_samples: int = 1000) -> Circuit:
    """
    Simplifies the circuit by first grouping gates based on partial truth tables using
    random input samples, then merging gates with the same operation and operands.

    :param circuit: - the original circuit to be simplified
    :param num_samples: - number of random input samples to use for initial grouping
    :return: - new simplified version of the circuit

    """

    def random_boolean():
        return random.choice([False, True])

    def get_partial_truth_table(circuit, inputs):
        assignment = {
            input_label: value for input_label, value in zip(circuit.inputs, inputs)
        }
        gate_values = circuit.evaluate_circuit(assignment)
        return {gate: gate_values[gate] for gate in circuit.gates}

    def group_gates_by_partial_truth_tables(circuit, num_samples):
        partial_truth_tables = collections.defaultdict(list)
        for _ in range(num_samples):
            inputs = [random_boolean() for _ in range(len(circuit.inputs))]
            partial_truth_table = get_partial_truth_table(circuit, inputs)
            for gate, output in partial_truth_table.items():
                partial_truth_tables[gate].append(output)

        grouped_gates = collections.defaultdict(list)
        for gate, outputs in partial_truth_tables.items():
            outputs_key = tuple(outputs)
            grouped_gates[outputs_key].append(gate)

        return [group for group in grouped_gates.values() if len(group) > 1]

    def merge_identical_gates_in_group(circuit, group):
        replacement_map = {}  # Maps original gate labels to new gate labels
        while True:
            merged = False
            new_group = []
            visited = set()
            for i, gate_label in enumerate(group):
                if gate_label in visited:
                    continue
                gate = circuit.get_gate(gate_label)
                found_duplicate = False
                for other_gate_label in group[i + 1 :]:
                    other_gate = circuit.get_gate(other_gate_label)
                    if gate.gate_type == other_gate.gate_type and set(
                        gate.operands
                    ) == set(other_gate.operands):
                        replacement_map[other_gate_label] = gate_label
                        found_duplicate = True
                        visited.add(other_gate_label)
                        merged = True
                if not found_duplicate:
                    new_group.append(gate_label)
                visited.add(gate_label)
            group = new_group
            if not merged:
                break

        new_circuit = Circuit()
        for gate_label, gate in circuit.gates.items():
            new_gate_label = replacement_map.get(gate_label, gate_label)
            new_operands = tuple(replacement_map.get(op, op) for op in gate.operands)
            if new_gate_label not in new_circuit.gates:
                new_gate = Gate(new_gate_label, gate.gate_type, new_operands)
                new_circuit.add_gate(new_gate)
            if gate_label in circuit.outputs:
                new_circuit.mark_as_output(new_gate_label)

        return new_circuit

    partial_groups = group_gates_by_partial_truth_tables(circuit, num_samples)

    for group in partial_groups:
        circuit = merge_identical_gates_in_group(circuit, group)

    return circuit


def remove_identities(circuit: Circuit) -> Circuit:
    """
    Simplifies the circuit by removing identities. Traverses the circuit and checks for
    identity conditions based on an internal dictionary.

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit

    """

    def get_sorted_gate_types(circuit: Circuit) -> list:
        return sorted(str(gate.gate_type) for gate in circuit.gates.values())

    while True:
        original_gate_types = get_sorted_gate_types(circuit)

        new_circuit = Circuit()
        replace_map = {}  # Maps original gate labels to new gate labels
        supported_identity_operations = {AND, NAND, XOR, NXOR, OR}
        identities = {
            AND: {
                frozenset([0, 0]): 'NOT_IDENTITY',  # AND(NOT(X), NOT(X)) = NOT(X)
                frozenset([0, 1]): 'ALWAYS_FALSE',  # AND(X, NOT(X)) = 0
                frozenset([1, 1]): 'IDENTITY',  # AND(X, X) = X
            },
            NAND: {
                frozenset([0, 0]): 'IDENTITY',  # NAND(NOT(X), NOT(X)) = X
                frozenset([0, 1]): 'ALWAYS_TRUE',  # NAND(X, NOT(X)) = 1
                frozenset([1, 1]): 'NOT_IDENTITY',  # NAND(X, X) = NOT(X)
            },
            XOR: {
                frozenset([0, 0]): 'ALWAYS_FALSE',  # XOR(NOT(X), NOT(X)) = 0
                frozenset([0, 1]): 'ALWAYS_TRUE',  # XOR(X, NOT(X)) = 1
                frozenset([1, 1]): 'ALWAYS_FALSE',  # XOR(X, X) = 0
            },
            NXOR: {
                frozenset([0, 0]): 'ALWAYS_TRUE',  # NXOR(NOT(X), NOT(X)) = 1
                frozenset([0, 1]): 'ALWAYS_FALSE',  # NXOR(X, NOT(X)) = 0
                frozenset([1, 1]): 'ALWAYS_TRUE',  # NXOR(X, X) = 1
            },
            OR: {
                frozenset([0, 0]): 'NOT_IDENTITY',  # OR(NOT(X), NOT(X)) = NOT(X)
                frozenset([0, 1]): 'ALWAYS_TRUE',  # OR(X, NOT(X)) = 1
                frozenset([1, 1]): 'IDENTITY',  # OR(X, X) = X
            },
        }

        def find_ancestor(gate_label):
            not_count = 1  # Add initial 1 to label it as not inverted in 1
            current_label = gate_label
            while circuit.get_gate(current_label).gate_type == NOT:
                not_count += 1
                current_label = circuit.get_gate(current_label).operands[0]
            return current_label, not_count % 2

        for gate_label, gate in circuit.gates.items():
            if gate.gate_type in supported_identity_operations:
                ancestor_data = [find_ancestor(op) for op in gate.operands]

                if len(ancestor_data) == 2:
                    ancestor_labels = [ancestor_data[0][0], ancestor_data[1][0]]
                    ancestor_states = [
                        circuit.get_gate(label).gate_type for label in ancestor_labels
                    ]

                    if set(ancestor_states) in [
                        {ALWAYS_TRUE},
                        {ALWAYS_FALSE},
                        {ALWAYS_TRUE, ALWAYS_FALSE},
                    ]:
                        values = []
                        for i, (label, not_count) in enumerate(ancestor_data):
                            value = ancestor_states[i] == ALWAYS_TRUE
                            if not_count % 2 == 0:
                                value = not value
                            values.append(value)
                        result_value = gate.operator(*values)
                        new_gate_type = ALWAYS_TRUE if result_value else ALWAYS_FALSE
                        new_gate = Gate(gate_label, new_gate_type, ())
                        new_circuit.add_gate(new_gate)
                        replace_map[gate_label] = gate_label

                if ancestor_data[0][0] == ancestor_data[1][0]:
                    operation_identity = identities.get(gate.gate_type)
                    if operation_identity:
                        identity_result = operation_identity.get(
                            frozenset([ancestor_data[0][1], ancestor_data[1][1]])
                        )

                        if identity_result == 'IDENTITY':
                            replace_map[gate_label] = ancestor_data[0][0]
                        elif identity_result == 'NOT_IDENTITY':
                            new_gate = Gate(gate_label, NOT, (ancestor_data[0][0],))
                            new_circuit.add_gate(new_gate)
                            replace_map[gate_label] = gate_label
                        elif identity_result == 'ALWAYS_TRUE':
                            new_gate = Gate(gate_label, ALWAYS_TRUE, ())
                            new_circuit.add_gate(new_gate)
                            replace_map[gate_label] = gate_label
                        elif identity_result == 'ALWAYS_FALSE':
                            new_gate = Gate(gate_label, ALWAYS_FALSE, ())
                            new_circuit.add_gate(new_gate)
                            replace_map[gate_label] = gate_label

            if gate_label not in new_circuit.gates:
                new_operands = tuple(replace_map.get(op, op) for op in gate.operands)
                new_gate = Gate(gate_label, gate.gate_type, new_operands)
                new_circuit.add_gate(new_gate)
                replace_map[gate_label] = gate_label

        for output_label in circuit.outputs:
            output_gate_label = replace_map.get(output_label, output_label)
            new_circuit.mark_as_output(output_gate_label)
        new_gate_types = get_sorted_gate_types(new_circuit)
        if original_gate_types == new_gate_types:
            break
        circuit = new_circuit

    return new_circuit


def clean(original_circuit: Circuit) -> Circuit:
    """
    Applies algorithms from this module consecutively in order
    to simplify given circuit.

    :param original_circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit

    """
    cleaned_from_identities = remove_identities(original_circuit)
    cleaned_from_equivalent_gates = delete_equivalent_gates(cleaned_from_identities)
    cleaned_from_leaves_double_not = remove_leaves_and_double_not(cleaned_from_equivalent_gates)
    return cleaned_from_leaves_double_not
