import logging
import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate


__all__ = [
    'remove_redundant_gates',
]


logger = logging.getLogger(__name__)


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

    # reconstruct circuit
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
