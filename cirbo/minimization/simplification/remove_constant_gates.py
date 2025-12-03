import logging
import typing as tp

import more_itertools

from cirbo.core.circuit import Circuit, Gate, gate, Label
from cirbo.core.circuit.transformer import Transformer

from .remove_redundant_gates import RemoveRedundantGates


__all__ = [
    'RemoveConstantGates',
]


logger = logging.getLogger(__name__)


# Constant gate types that this transformer handles.
_CONST_GATES = (gate.ALWAYS_TRUE, gate.ALWAYS_FALSE)

# Mapping from (out_when_var_is_0, out_when_var_is_1) to the resulting gate type.
# Used to determine the simplified gate type when one operand is constant.
_OUTPUTS_TO_GATE_TYPE: dict[tuple[int, int], gate.GateType] = {
    (0, 0): gate.ALWAYS_FALSE,
    (0, 1): gate.IFF,
    (1, 0): gate.NOT,
    (1, 1): gate.ALWAYS_TRUE,
}


def _get_const_value(gate_type: gate.GateType) -> int:
    return 1 if gate_type == gate.ALWAYS_TRUE else 0


def _simplify_unary_gate(
    original_gate: Gate,
    operand_gate_type: gate.GateType,
) -> tuple[gate.GateType, tuple[Label, ...]]:
    """Simplify a unary gate (IFF or NOT) when its operand is a constant."""
    const_val = _get_const_value(operand_gate_type)

    if original_gate.gate_type == gate.IFF:
        # IFF(const) = const
        new_type = operand_gate_type
    elif original_gate.gate_type == gate.NOT:
        # NOT(ALWAYS_TRUE) = ALWAYS_FALSE, NOT(ALWAYS_FALSE) = ALWAYS_TRUE
        new_type = gate.ALWAYS_FALSE if const_val == 1 else gate.ALWAYS_TRUE
    else:
        raise ValueError(f"Unsupported unary gate type: {original_gate.gate_type}")

    return new_type, ()


def _simplify_binary_gate(
    original_gate: Gate,
    const_operand_idx: int,
    const_value: int,
) -> tuple[gate.GateType, tuple[Label, ...]]:
    """Simplify a binary gate when one of its operands is a constant."""
    # compute output when the non-constant operand is 0 and when it's 1
    if const_operand_idx == 0:
        out_0 = original_gate.operator(const_value, 0)
        out_1 = original_gate.operator(const_value, 1)
    else:
        out_0 = original_gate.operator(0, const_value)
        out_1 = original_gate.operator(1, const_value)

    new_type = _OUTPUTS_TO_GATE_TYPE[(int(out_0), int(out_1))]

    if new_type in _CONST_GATES:
        # gate became constant - no operands needed
        new_operands: tuple[Label, ...] = ()
    else:
        # gate depends on the non-constant operand only
        non_const_idx = 1 - const_operand_idx
        new_operands = (original_gate.operands[non_const_idx],)

    return new_type, new_operands


class RemoveConstantGates(Transformer):
    """
    Simplifies the circuit by propagating and removing constant gates.

    When a gate has a constant (ALWAYS_TRUE or ALWAYS_FALSE) operand, the transformer
    computes the simplified form of that gate based on the truth table evaluation
    with the known constant value.

    Examples:
        - AND(x, ALWAYS_TRUE) -> x
        - AND(x, ALWAYS_FALSE) -> ALWAYS_FALSE
        - OR(x, ALWAYS_TRUE) -> ALWAYS_TRUE
        - OR(x, ALWAYS_FALSE) -> x
        - NOT(ALWAYS_TRUE) -> ALWAYS_FALSE
        - XOR(x, ALWAYS_TRUE) -> NOT(x)
        - XOR(x, ALWAYS_FALSE) -> x

    Note: output gate labels may change after this method is applied, but their
    order will be preserved.

    """

    __idempotent__: bool = True

    def __init__(self):
        super().__init__(post_transformers=(RemoveRedundantGates(),))

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        _new_circuit = Circuit()

        # mapping from original gate labels to their simplified labels.
        # if a gate simplifies to another gate (e.g., AND(x, TRUE) -> x),
        # this maps the original gate label to the simplified one.
        _label_remap: dict[Label, Label] = {}

        # mapping from gate labels to their (possibly new) gate types.
        # used to track when gates become constants.
        _gate_types: dict[Label, gate.GateType] = {}

        def _get_remapped_label(label: Label) -> Label:
            while label in _label_remap:
                label = _label_remap[label]
            return label

        def _process_gate(_gate: Gate, _: tp.Mapping):
            nonlocal _new_circuit, _label_remap, _gate_types

            # remap operands to their simplified labels
            remapped_operands = tuple(_get_remapped_label(op) for op in _gate.operands)

            # track the gate type (initially the original type)
            current_type = _gate.gate_type
            current_operands = remapped_operands

            # check if any operand is a constant gate
            const_operand_infos: list[tuple[int, int]] = []
            for idx, op_label in enumerate(remapped_operands):
                op_type = _gate_types.get(op_label)
                if op_type in _CONST_GATES:
                    const_operand_infos.append((idx, _get_const_value(op_type)))

            # simplify if we have constant operands
            if const_operand_infos and current_type not in (gate.INPUT, *_CONST_GATES):
                if len(current_operands) == 1:
                    # unary gate with constant operand
                    const_type = _gate_types[remapped_operands[0]]
                    current_type, current_operands = _simplify_unary_gate(
                        _gate, const_type
                    )
                elif len(current_operands) == 2 and len(const_operand_infos) == 1:
                    # binary gate with one constant operand
                    const_idx, const_val = const_operand_infos[0]
                    current_type, current_operands = _simplify_binary_gate(
                        _gate, const_idx, const_val
                    )
                elif len(current_operands) == 2 and len(const_operand_infos) == 2:
                    # binary gate with both operands being constants
                    const_0 = const_operand_infos[0][1]
                    const_1 = const_operand_infos[1][1]
                    result = _gate.operator(const_0, const_1)
                    current_type = gate.ALWAYS_TRUE if result else gate.ALWAYS_FALSE
                    current_operands = ()

            # store the gate type for later reference
            _gate_types[_gate.label] = current_type

            # if the gate became an IFF (buffer), remap to its operand directly
            if current_type == gate.IFF and len(current_operands) == 1:
                _label_remap[_gate.label] = current_operands[0]
                # still add the gate to the circuit; it will be removed by
                # RemoveRedundantGates if not needed
                _new_circuit.emplace_gate(
                    label=_gate.label,
                    gate_type=current_type,
                    operands=current_operands,
                )
            else:
                _new_circuit.emplace_gate(
                    label=_gate.label,
                    gate_type=current_type,
                    operands=current_operands,
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

        # mark outputs, applying any label remappings
        _new_circuit.set_outputs([_get_remapped_label(out) for out in circuit.outputs])

        return _new_circuit
