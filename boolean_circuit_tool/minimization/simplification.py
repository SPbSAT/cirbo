"""
Module contains functions for simplification of boolean circuits.

Each function returns a new Circuit instance that represents the simplified version of
the input circuit.

"""

import collections
import functools
import itertools
import operator
import random
import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit import Circuit, GateState
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Gate,
    IFF,
    Label,
    LIFF,
    LNOT,
    NAND,
    NOT,
    NXOR,
    OR,
    RIFF,
    RNOT,
    XOR,
)

__all__ = [
    'remove_redundant_gates',
    'collapse_unary_operators',
    'delete_equivalent_gates',
    'merge_same_successors',
    'remove_identities',
    'cleanup',
]


# Utility that helps to extract significant operand.
_unary_to_operand_getter = {
    NOT: operator.itemgetter(0),
    LNOT: operator.itemgetter(0),
    RNOT: operator.itemgetter(1),
    IFF: operator.itemgetter(0),
    LIFF: operator.itemgetter(0),
    RIFF: operator.itemgetter(1),
}


def remove_redundant_gates(
    circuit: Circuit,
    *,
    allow_inputs_removal: bool = False,
) -> Circuit:
    """
    Simplifies the circuit by removing gates which are not reachable from output gates
    (e.g. have no effect on output of a circuit).

    Traverses the circuit recursively, starting from the output gates, and rebuilds
    the circuit without unused gates.

    Note: will preserve all Output gate markers and their ordering.
    Note: will preserve Inputs ordering, even if some inputs will be
          cleaned when given `allow_inputs_removal=True`.

    :param circuit: the original circuit to be simplified.
    :param allow_inputs_removal: flag that controls if redundant inputs should
           be removed or not.
    :return: new simplified version of the circuit.

    """
    _new_circuit = Circuit()

    def _on_exit_hook_impl(gate: Gate, _: tp.Mapping):
        nonlocal _new_circuit
        _new_circuit.emplace_gate(
            label=gate.label,
            gate_type=gate.gate_type,
            operands=gate.operands,
        )

    # reconstruct circuit from
    more_itertools.consume(
        circuit.dfs(
            circuit.outputs,
            on_exit_hook=_on_exit_hook_impl,
        )
    )

    # add complementary inputs
    if not allow_inputs_removal:
        _new_circuit.add_inputs(
            [
                input_label
                for input_label in circuit.inputs
                if not _new_circuit.has_gate(input_label)
            ]
        )

    # reorder inputs according to original order
    _new_circuit.set_inputs(
        [
            input_label
            for input_label in circuit.inputs
            if input_label in _new_circuit.inputs
        ]
    )

    # mark same outputs as in original circuit (all of them were visited)
    _new_circuit.set_outputs(circuit.outputs)

    return _new_circuit


def collapse_unary_operators(circuit: Circuit) -> Circuit:
    """
    Simplifies the circuit by collapsing consecutive unary gates . Collapses double NOTs
    A = NOT(NOT(B)) => A = B and eliminates IFFs.

    Traverses the circuit recursively, starting from the output gates, and rebuilds
    the circuit collapsing paths through redundant unary gates.

    Notes: Output gates labels may change after this method is applied, but their
    order will be preserved.

    Note: gates are not removed after this method is applied, and only operands of
    gates are revamped. It is recommended to call `remove_redundant_gates` right
    after this method.

    Note: will also remap LNOT, RNOT, LIFF, RIFF to their transitive significant
    operand if path reduction is possible.

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

    """
    _new_circuit = Circuit()

    # redirection links that will
    # allow us to collapse paths.
    #
    # contains to predecessor path to which consists of even number of NOTs
    _not_to_even_parent: dict[Label, Label] = {}
    # contains to predecessor path to which consists of odd number of NOTs
    _not_to_odd_parent: dict[Label, Label] = {}
    # contains to predecessor path to which consists of only of IFFs
    _iff_to_parent: dict[Label, Label] = {}

    # iterate from inputs to outputs in topsort
    # order to collect redirection links.
    for _gate in circuit.top_sort(inverse=True):
        if (
            False
            or _gate.gate_type == NOT
            or _gate.gate_type == LNOT
            or _gate.gate_type == RNOT
        ):
            _oper = _unary_to_operand_getter[_gate.gate_type](_gate.operands)
            if _oper in _not_to_odd_parent:
                _not_to_even_parent[_gate.label] = _not_to_odd_parent[_oper]
            _not_to_odd_parent[_gate.label] = _not_to_even_parent.get(_oper, _oper)

        if (
            False
            or _gate.gate_type == IFF
            or _gate.gate_type == LIFF
            or _gate.gate_type == RIFF
        ):
            _oper = _unary_to_operand_getter[_gate.gate_type](_gate.operands)
            _iff_to_parent[_gate.label] = _iff_to_parent.get(_oper, _oper)

    # remap gates to equivalent but closer ones.
    def _remap_gate(op_label: Label):
        nonlocal circuit, _not_to_even_parent, _iff_to_parent
        _op_gate = circuit.get_gate(op_label)

        if (
            False
            or _op_gate.gate_type == NOT
            or _op_gate.gate_type == LNOT
            or _op_gate.gate_type == RNOT
        ):
            return _not_to_even_parent.get(op_label, op_label)
        elif (
            False
            or _op_gate.gate_type == IFF
            or _op_gate.gate_type == LIFF
            or _op_gate.gate_type == RIFF
        ):
            return _iff_to_parent.get(op_label, op_label)
        else:
            return op_label

    # rebuild circuit from inputs to outputs with remapping.
    def _on_exit_hook_impl(gate: Gate, _: tp.Mapping):
        nonlocal _new_circuit, _not_to_even_parent, _iff_to_parent
        _new_circuit.emplace_gate(
            label=gate.label,
            gate_type=gate.gate_type,
            operands=tuple(map(_remap_gate, gate.operands)),
        )

    # reconstruct circuit from
    more_itertools.consume(
        circuit.dfs(
            circuit.outputs,
            on_exit_hook=_on_exit_hook_impl,
        )
    )

    # reorder inputs according to original order
    _new_circuit.set_inputs(circuit.inputs)

    # mark outputs in new circuit by remapping them to their equivalent ones.
    _new_circuit.set_outputs(list(map(_remap_gate, circuit.outputs)))

    return _new_circuit


def _find_equivalent_gates(circuit: Circuit) -> list[list[str]]:
    """
    Identifies and groups equivalent gates within the circuit based on their full truth
    tables.

    :param circuit: the circuit to analyze for equivalent gates
    :return: a list of groups, each containing labels of equivalent gates

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

    :param circuit: the original circuit
    :param equivalent_groups: groups of equivalent gates
    :return: a new circuit with equivalent gates replaced

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

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

    """
    equivalent_gate_groups = _find_equivalent_gates(circuit)
    return _replace_equivalent_gates(circuit, equivalent_gate_groups)


def merge_same_successors(circuit: Circuit, num_samples: int = 1000) -> Circuit:
    """
    Simplifies the circuit by first grouping gates based on partial truth tables using
    random input samples, then merging gates with the same operation and operands.

    :param circuit: the original circuit to be simplified
    :param num_samples: number of random input samples to use for initial grouping
    :return: new simplified version of the circuit

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

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

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


def cleanup(circuit: Circuit) -> Circuit:
    """
    Applies several simplification algorithms from this module consecutively in order to
    simplify provided circuit.

    :param circuit: the original circuit to be simplified
    :return: new simplified version of the circuit

    """
    return functools.reduce(
        lambda _circ, _method: _method(circuit),  # type: ignore
        [
            remove_identities,
            delete_equivalent_gates,
            remove_redundant_gates,
            collapse_unary_operators,
            remove_identities,
        ],
        circuit,
    )
