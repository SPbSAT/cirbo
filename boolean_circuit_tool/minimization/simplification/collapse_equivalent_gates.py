import collections
import itertools
import logging
import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit import Circuit, GateState
from boolean_circuit_tool.core.circuit.gate import Gate, Label
from boolean_circuit_tool.core.circuit.transformer import Transformer
from boolean_circuit_tool.minimization.simplification.remove_redundant_gates import (
    RemoveRedundantGates,
)


__all__ = [
    'CollapseEquivalentGates',
]


logger = logging.getLogger(__name__)


class CollapseEquivalentGates(Transformer):
    """
    Finds groups of equivalent gates using the full truth table comparison and replaces
    them with a single gate, updating all the references to the old ones.

    Warning: the execution time grows exponentially as the number of inputs increases.
    For circuits with more than 20 inputs it is recommended to use alternative
    `CollapseDuplicateGates` methods.

    """

    def __init__(self):
        super().__init__(post_transformers=(RemoveRedundantGates(),))

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        equivalent_gate_groups = _find_equivalent_gates_groups(circuit)
        return _replace_equivalent_gates(circuit, equivalent_gate_groups)


def _find_equivalent_gates_groups(circuit: Circuit) -> list[list[Label]]:
    """
    Identifies and groups equivalent gates within the circuit based on their full truth
    tables.

    :param circuit: the circuit to analyze for equivalent gates
    :return: a list of groups, each containing labels of equivalent gates

    """
    # Evaluate truth table of each gate in the circuit.
    _gate_to_tt = collections.defaultdict(list)
    for _input_values in itertools.product((False, True), repeat=circuit.input_size):
        _input_assignment: dict[str, GateState] = {
            input_label: value
            for input_label, value in zip(circuit.inputs, _input_values)
        }
        _full_assignment = circuit.evaluate_full_circuit(_input_assignment)
        for gate_label, value in _full_assignment.items():
            _gate_to_tt[gate_label].append(value)

    # Find which gates have same truth table.
    _tt_to_gates = collections.defaultdict(list)
    for gate_label, truth_table in _gate_to_tt.items():
        _tt_to_gates[tuple(truth_table)].append(gate_label)

    # Find groups of equivalent gates.
    equivalent_groups = [gates for gates in _tt_to_gates.values() if len(gates) > 1]

    return equivalent_groups


def _replace_equivalent_gates(
    circuit: Circuit,
    equivalent_groups: tp.Iterable[tp.Collection[Label]],
) -> Circuit:
    """
    Reconstructs the circuit by replacing all links to equivalent gates identified by a
    link to a single representative of each equivalence group.

    :param circuit: the original circuit
    :param equivalent_groups: groups of equivalent gates
    :return: a new circuit with equivalent gates replaced

    """
    _new_circuit = Circuit()

    # Maps original gate labels to new gate labels
    _old_to_new_gate = {}

    # Collect replacements map.
    for group in equivalent_groups:
        if len(group) <= 1:
            logger.debug(
                f"Got equivalence group with only {len(group)} elements: {group}.",
            )
            continue

        _group_iter = iter(group)
        keep = next(_group_iter)
        for gate_to_replace in _group_iter:
            _old_to_new_gate[gate_to_replace] = keep

    # map gate label to its new name.
    def _remap_gate(gate_label: Label):
        nonlocal _old_to_new_gate
        return _old_to_new_gate.get(gate_label, gate_label)

    # rebuild circuit from inputs to outputs with remapping.
    def _on_exit_hook_impl(gate: Gate, _: tp.Mapping):
        nonlocal _new_circuit, _old_to_new_gate
        # Either new or same label.
        _new_label = _remap_gate(gate.label)

        # If circuit already contains "keep" gate,
        # no need to add it again, just return.
        if _new_circuit.has_gate(_new_label):
            return

        if gate.label not in _old_to_new_gate:
            # If gate doesn't need to be remapped
            # just add it to circuit.
            _new_circuit.emplace_gate(
                label=_new_label,
                gate_type=gate.gate_type,
                operands=tuple(map(_remap_gate, gate.operands)),
            )
            return

        # Need to add "keep" gate after first occurrence
        # of its equivalent gate to not break a topsort
        # order when adding its users.
        _new_circuit.get_gate(_new)
        _new_circuit.emplace_gate(
            label=_new_label,
            gate_type=gate.gate_type,
            operands=tuple(map(_remap_gate, gate.operands)),
        )
        return

    # reconstruct circuit
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
