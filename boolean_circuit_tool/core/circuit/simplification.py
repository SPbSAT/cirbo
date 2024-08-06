import itertools
from collections import defaultdict
from boolean_circuit_tool.core.circuit import Circuit, GateType, Gate

from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Gate,
    GEQ,
    GT,
    INPUT,
    LEQ,
    LNOT,
    LT,
    NOT,
    OR,
    RNOT,
    XOR,
)


def remove_leaves_and_double_not(circuit: Circuit) -> Circuit:
    """
    Simplifies the circuit by removing leaves and consecutive NOT gates.
    Traverses the circuit recursively, starting from the output gates,
    and rebuilds the circuit without redundant NOT gates and unused gates.

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit
    """
    new_circuit = Circuit()
    visited = set()
    gate_map = {}

    def dfs(gate_label):
        if gate_label in visited:
            return gate_map.get(gate_label)
        visited.add(gate_label)

        original_gate = circuit.get_element(gate_label)
        operands = []

        if original_gate.gate_type == NOT:
            operand_label = original_gate.operands[0]
            operand_gate = circuit.get_element(operand_label)
            if operand_gate.gate_type == NOT:
                result_label = dfs(operand_gate.operands[0])
                gate_map[gate_label] = result_label
                return result_label
            else:
                operands.append(dfs(operand_label))
        else:
            operands = [dfs(op_label) for op_label in original_gate.operands]

        if gate_label not in gate_map:
            new_gate_label = gate_label
            new_gate = Gate(new_gate_label, original_gate.gate_type, tuple(operands))
            new_circuit.add_gate(new_gate)
            gate_map[gate_label] = new_gate_label

        return gate_map[gate_label]

    for output_label in circuit.outputs:
        output_gate_label = dfs(output_label)
        new_circuit.mark_as_output(output_gate_label)

    return new_circuit


def evaluate_circuit(circuit: Circuit, inputs: list[bool]) -> dict:
    """
    Evaluate the circuit for a given set of input values and computes
    the output for all gates. This function ensures all gates are calculated
    only once by caching their values.

    :param circuit: - the circuit to be evaluated
    :param inputs: - list of boolean inputs corresponding to the circuit inputs
    :return: - a dictionary with gate labels as keys and their computed values as values
    """
    gate_values = {gate: None for gate in circuit.elements}
    for gate_label, value in zip(circuit.inputs, inputs):
        gate_values[gate_label] = value

    def compute_gate_value(gate_label):
        if gate_values[gate_label] is not None:
            return gate_values[gate_label]
        gate = circuit.get_element(gate_label)
        operand_values = [compute_gate_value(operand) for operand in gate.operands]
        gate_values[gate_label] = gate.operator(*operand_values)

        return gate_values[gate_label]

    for gate_label in circuit.elements:
        compute_gate_value(gate_label)

    return gate_values


def find_equivalent_gates(circuit: Circuit) -> list[list[str]]:
    """
    Identifies and groups equivalent gates within the circuit based on their truth tables.

    :param circuit: - the circuit to analyze for equivalent gates
    :return: - a list of groups, each containing labels of equivalent gates
    """
    input_size = len(circuit.inputs)
    input_combinations = list(itertools.product([False, True], repeat=input_size))
    gate_truth_tables = defaultdict(list)

    for inputs in input_combinations:
        gate_values = evaluate_circuit(circuit, inputs)

        for gate_label, output in gate_values.items():
            gate_truth_tables[gate_label].append(output)

    truth_table_to_gates = defaultdict(list)
    for gate_label, truth_table in gate_truth_tables.items():
        truth_key = tuple(truth_table)
        truth_table_to_gates[truth_key].append(gate_label)
    equivalent_groups = [gates for gates in truth_table_to_gates.values() if len(gates) > 1]

    return equivalent_groups


def replace_gate(old_label, new_label, circuit):
    for gate in circuit.elements.values():
        new_operands = [new_label if x == old_label else x for x in gate.operands]
        if new_operands != gate.operands:
            updated_gate = Gate(gate.label, gate.gate_type, tuple(new_operands))
            circuit.replace_gate(gate.label, updated_gate)


def replace_equivalent_gates(circuit: Circuit, equivalent_groups: list[list[str]]) -> Circuit:
    """
    Reconstructs the circuit by replacing all equivalent gates identified by `find_equivalent_gates`
    with a single representative from each group, updating references accordingly.

    :param circuit: - the original circuit
    :param equivalent_groups: - groups of equivalent gates
    :return: - a new circuit with equivalent gates replaced
    """
    replacement_map = {}
    new_circuit = Circuit()

    for group in equivalent_groups:
        if len(group) > 1:
            keep = group[0]
            for gate_to_replace in group[1:]:
                replacement_map[gate_to_replace] = keep

    for gate_label, gate in circuit.elements.items():
        new_gate_label = replacement_map.get(gate_label, gate_label)
        new_operands = tuple(replacement_map.get(operand, operand) for operand in gate.operands)

        if new_gate_label not in new_circuit.elements:
            new_gate = Gate(new_gate_label, gate.gate_type, new_operands)
            new_circuit.add_gate(new_gate)

        if gate_label in circuit.outputs:
            if new_gate_label not in new_circuit.outputs:
                new_circuit.mark_as_output(new_gate_label)

    return new_circuit


def simplify_by_deleting_equivalent_gates(circuit: Circuit) -> Circuit:
    """
    Finds groups of equivalent gates using the full truth table comparison
    and replaces them with a single gate, updating all the references to the old ones.

    :param circuit: - the original circuit to be simplified
    :return: - new simplified version of the circuit
    """

    equivalent_gate_groups = find_equivalent_gates(circuit)
    return replace_equivalent_gates(circuit, equivalent_gate_groups)
