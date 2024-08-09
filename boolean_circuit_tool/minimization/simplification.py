"""
Module contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

import collections
import itertools
import random

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, NOT

__all__ = [
    'remove_leaves_and_double_not',
    'simplify_by_deleting_equivalent_gates',
    'merge_same_gates',
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
    visited = set()  # Stores the labels of gates that have already been visited
    gate_map = (
        {}
    )  # Maps original gate labels to new gate labels or the labels of the gates that replace them

    def _dfs(gate_label):
        if gate_label in visited:
            return gate_map.get(gate_label)
        visited.add(gate_label)

        original_gate = circuit.get_gate(gate_label)
        operands = []

        if original_gate.gate_type == NOT:
            operand_label = original_gate.operands[0]
            operand_gate = circuit.get_gate(operand_label)
            if operand_gate.gate_type == NOT:
                result_label = _dfs(operand_gate.operands[0])
                gate_map[gate_label] = result_label
                return result_label
            else:
                operands.append(_dfs(operand_label))
        else:
            operands = [_dfs(op_label) for op_label in original_gate.operands]

        if gate_label not in gate_map:
            new_gate_label = gate_label
            new_gate = Gate(new_gate_label, original_gate.gate_type, tuple(operands))
            new_circuit.add_gate(new_gate)
            gate_map[gate_label] = new_gate_label

        return gate_map[gate_label]

    for output_label in circuit.outputs:
        output_gate_label = _dfs(output_label)
        new_circuit.mark_as_output(output_gate_label)

    return new_circuit


def _evaluate_circuit(circuit: Circuit, inputs: list[bool]) -> dict:
    """
    Evaluate the circuit for a given set of input values and computes the output for all
    gates. This function ensures all gates are calculated only once by caching their
    values.

    :param circuit: - the circuit to be evaluated
    :param inputs: - list of boolean inputs corresponding to the circuit inputs
    :return: - a dictionary with gate labels as keys and their computed values as values

    """
    gate_values = {gate: None for gate in circuit.gates}
    for gate_label, value in zip(circuit.inputs, inputs):
        gate_values[gate_label] = value

    def compute_gate_value(gate_label):
        if gate_values[gate_label] is not None:
            return gate_values[gate_label]
        gate = circuit.get_gate(gate_label)
        operand_values = [compute_gate_value(operand) for operand in gate.operands]
        gate_values[gate_label] = gate.operator(*operand_values)

        return gate_values[gate_label]

    for gate_label in circuit.gates:
        compute_gate_value(gate_label)

    return gate_values


def _find_equivalent_gates(circuit: Circuit) -> list[list[str]]:
    """
    Identifies and groups equivalent gates within the circuit based on their truth
    tables.

    :param circuit: - the circuit to analyze for equivalent gates
    :return: - a list of groups, each containing labels of equivalent gates

    """
    input_size = len(circuit.inputs)
    input_combinations = list(itertools.product([False, True], repeat=input_size))
    gate_truth_tables = collections.defaultdict(list)

    for inputs in input_combinations:
        gate_values = _evaluate_circuit(circuit, inputs)

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


def _replace_gate(old_label, new_label, circuit):
    for gate in circuit.gates.values():
        new_operands = [new_label if x == old_label else x for x in gate.operands]
        if new_operands != gate.operands:
            updated_gate = Gate(gate.label, gate.gate_type, tuple(new_operands))
            circuit.replace_gate(gate.label, updated_gate)


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
    replacement_map = (
        {}
    )  # Maps each gate label that needs to be replaced to the label of the gate that will replace it
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


def simplify_by_deleting_equivalent_gates(circuit: Circuit) -> Circuit:
    """
    Finds groups of equivalent gates using the full truth table comparison and replaces
    them with a single gate, updating all the references to the old ones.

    Warning: the execution time grows exponentially as the number of inputs increases.
    For circuits with more than 20 inputs it is recommended to use merge_same_gates().

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit

    """
    equivalent_gate_groups = _find_equivalent_gates(circuit)
    return _replace_equivalent_gates(circuit, equivalent_gate_groups)


def merge_same_gates(circuit: Circuit, num_samples: int = 1000) -> Circuit:
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
        gate_values = _evaluate_circuit(circuit, inputs)
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
        replacement_map = {}
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
