import collections
import logging
import random
import warnings

from boolean_circuit_tool.core.circuit import Circuit
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


__all__ = []

logger = logging.getLogger(__name__)


def collapse_equivalent_gates_sparse(
    circuit: Circuit,
    *,
    num_samples: int = 1000,
) -> Circuit:
    """
    Simplifies the circuit by first grouping gates based on partial truth tables using
    random input samples, then merging gates with the same operation and operands.

    :param circuit: the original circuit to be simplified
    :param num_samples: number of random input samples to use for initial grouping
    :return: new simplified version of the circuit

    """
    warnings.warn(
        "This method is yet unstable and is not ready to be used",
        DeprecationWarning,
    )

    def random_boolean():
        return random.choice([False, True])

    def get_partial_truth_table(circuit, inputs):
        assignment = {
            input_label: value for input_label, value in zip(circuit.inputs, inputs)
        }
        gate_values = circuit.evaluate_full_circuit(assignment)
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

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

    """
    warnings.warn(
        "This method is yet unstable and is not ready to be used",
        DeprecationWarning,
    )

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
