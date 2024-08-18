import logging
import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate
from boolean_circuit_tool.core.circuit.transformer import Transformer


__all__ = [
    'RemoveRedundantGates',
]


logger = logging.getLogger(__name__)


class RemoveRedundantGates(Transformer):
    """
    Simplifies the circuit by removing gates which are not reachable from output gates
    (e.g. have no effect on output of a circuit).

    Traverses the circuit recursively, starting from the output gates, and rebuilds
    the circuit without unused gates.

    Note: will preserve all Output gate markers and their ordering.
    Note: will preserve Inputs ordering, even if some inputs will be
          cleaned when given `allow_inputs_removal=True`.

    """

    __idempotent__: bool = True

    def __init__(
        self,
        *,
        allow_inputs_removal: bool = False,
    ):
        """
        :param allow_inputs_removal: flag that controls if redundant inputs should
               be removed or not.

        """
        super().__init__()
        self._allow_inputs_removal = allow_inputs_removal

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified.
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
        if not self._allow_inputs_removal:
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

    def __eq__(self, other: tp.Any):
        if not isinstance(other, RemoveRedundantGates):
            return NotImplemented

        return (
            super().__eq__(other)
            and self._allow_inputs_removal == other._allow_inputs_removal
        )
