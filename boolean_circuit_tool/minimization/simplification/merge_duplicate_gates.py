import logging
import typing as tp

import more_itertools

from boolean_circuit_tool.core import Gate
from boolean_circuit_tool.core.circuit import Circuit, gate, Label
from boolean_circuit_tool.core.circuit.transformer import Transformer
from .remove_redundant_gates import RemoveRedundantGates


__all__ = [
    'MergeDuplicateGates',
]


logger = logging.getLogger(__name__)


class MergeDuplicateGates(Transformer):
    """
    Finds literal duplicates (gates which have same type and operands) and relink their
    users to only one of them.

    Note: will also merge all operators that have no operands (e.g. ALWAYS_TRUE)

    """

    def __init__(self):
        super().__init__(post_transformers=(RemoveRedundantGates(),))

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        _new_circuit = Circuit()
        # Hold mapping of gate signature to the first found duplicate.
        _signature_to_duplicate: dict[tuple, Label] = {}

        # build signature based on gate
        def _to_signature(_gate: Gate) -> tuple:
            _operands = (
                tuple(sorted(_gate.operands))
                if _gate.gate_type.is_symmetric
                else _gate.operands
            )
            return (_gate.gate_type,) + _operands

        # build signature based on label of gate in original circuit
        def _label_to_signature(_label: Label) -> tuple:
            nonlocal circuit
            return _to_signature(circuit.get_gate(_label))

        # map gate label to its new name.
        def _get_gate_new_name(_label: Label):
            nonlocal _signature_to_duplicate
            return _signature_to_duplicate.get(_label_to_signature(_label), _label)

        def _process_gate(_gate: Gate, _: tp.Mapping):
            nonlocal _new_circuit, _signature_to_duplicate

            # Do not merge inputs.
            if _gate.gate_type == gate.INPUT:
                _new_circuit.add_inputs([_gate.label])
                return

            _sig = _to_signature(_gate)
            # memorize gate is no gate with same signature were met before.
            # all duplicates will be removed on post-transformation step.
            _signature_to_duplicate.setdefault(_sig, _gate.label)

            _new_circuit.emplace_gate(
                label=_gate.label,
                gate_type=_gate.gate_type,
                operands=tuple(map(_get_gate_new_name, _gate.operands)),
            )

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

        # mark same outputs as in original circuit (all of them were visited)
        _new_circuit.set_outputs(list(map(_get_gate_new_name, circuit.outputs)))

        return _new_circuit
