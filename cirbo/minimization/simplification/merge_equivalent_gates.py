import collections
import dataclasses
import logging
import typing as tp

import more_itertools

from cirbo.core.circuit import Circuit, Gate, Label
from cirbo.core.circuit.transformer import Transformer
from cirbo.minimization.simplification.remove_redundant_gates import (
    RemoveRedundantGates,
)


__all__ = [
    'MergeEquivalentGates',
]


logger = logging.getLogger(__name__)


class MergeEquivalentGates(Transformer):
    """
    Finds groups of equivalent gates using the full truth table comparison and replaces
    them with a single gate, updating all the references to the old ones.

    Warning: the execution time grows exponentially as the number of inputs increases.
    For circuits with more than 20 inputs it is recommended to use alternative
    `MergeDuplicateGates` methods.

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
    _gate_to_tt = circuit.get_gates_truth_table()

    # Find which gates have same truth table.
    _tt_to_gates = collections.defaultdict(list)
    for gate_label, truth_table in _gate_to_tt.items():
        _tt_to_gates[tuple(truth_table)].append(gate_label)

    # Find groups of equivalent gates.
    equivalent_groups = [gates for gates in _tt_to_gates.values() if len(gates) > 1]

    return equivalent_groups


@dataclasses.dataclass
class _Keep:
    """
    A representative element for the group.

    If holds None, then no elements of the group were reconstructed yet. When the first
    element of the group is rebuild, It will be set as Keep.

    """

    value: tp.Optional[str] = None

    def set_or_get_existing(self, label: str) -> str:
        if self.value is None:
            self.value = label

        return self.value


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

        keep = _Keep()
        for gate_to_replace in group:
            _old_to_new_gate[gate_to_replace] = keep

    # map gate label to its new name and sets Keep when needed.
    def _get_gate_new_name(_label: Label):
        nonlocal _old_to_new_gate

        if _label not in _old_to_new_gate:
            return _label

        _keep = _old_to_new_gate[_label]
        return _keep.set_or_get_existing(_label)

    # rebuild circuit from inputs to outputs with remapping.
    def _process_gate(_gate: Gate, _: tp.Mapping):
        nonlocal _new_circuit, _old_to_new_gate

        # Add all gates, even equivalent ones, but link
        # users of the latest to "keep" representative.
        _new_circuit.emplace_gate(
            label=_gate.label,
            gate_type=_gate.gate_type,
            operands=tuple(map(_get_gate_new_name, _gate.operands)),
        )
        return

    # reconstruct circuit
    more_itertools.consume(
        circuit.dfs(
            circuit.outputs,
            on_exit_hook=_process_gate,
            unvisited_hook=_process_gate,
            topsort_unvisited=True,
        )
    )

    # reorder inputs according to original order
    _new_circuit.set_inputs(circuit.inputs)

    # mark outputs in new circuit by remapping them to their equivalent ones.
    _new_circuit.set_outputs(list(map(_get_gate_new_name, circuit.outputs)))

    return _new_circuit
