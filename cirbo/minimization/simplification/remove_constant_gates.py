import logging
import typing as tp
import copy

from cirbo.core.circuit import Circuit, gate
from cirbo.core.circuit.gate import Gate
from cirbo.core.circuit.transformer import Transformer
from cirbo.minimization import RemoveRedundantGates

__all__ = [
    'RemoveConstantGates'
]

logger = logging.getLogger(__name__)

_outputs_to_gate_type: tp.Dict[int, tp.Dict[int, gate.GateType]] = {
    0: {
        0: gate.ALWAYS_FALSE,
        1: gate.IFF,
    },
    1: {
        0: gate.NOT,
        1: gate.ALWAYS_TRUE
    }
}

CONST_GATES = (gate.ALWAYS_TRUE, gate.ALWAYS_FALSE)


class RemoveConstantGates(Transformer):
    """
    TODO: write docstring
    """

    __idempotent__: bool = True

    def __init__(self):
        super().__init__(
            post_transformers=(RemoveRedundantGates(),)
        )

    @staticmethod
    def _simplify_unary_user_gate(user_gate: Gate, const_gate: Gate) -> Gate:
        assert user_gate.gate_type in [gate.IFF, gate.NOT]
        if user_gate.gate_type == gate.IFF:
            return Gate(user_gate.label, const_gate.gate_type, tuple())
        elif const_gate.gate_type == gate.ALWAYS_TRUE:
            return Gate(user_gate.label, gate.ALWAYS_FALSE, tuple())
        else:
            return Gate(user_gate.label, gate.ALWAYS_TRUE, tuple())

    @staticmethod
    def _simplify_binary_user_gate(circuit: Circuit, user_gate: Gate, const_gate: Gate) -> Gate:
        const_idx = user_gate.operands.index(const_gate.label)
        const_val = 1 if const_gate.gate_type == gate.ALWAYS_TRUE else 0
        out_0, out_1 = [
            user_gate.operator(*([const_val, v] if const_idx == 0 else [v, const_val]))
            for v in (0, 1)
        ]
        new_type = _outputs_to_gate_type[out_0][out_1]
        if new_type in CONST_GATES:
            new_operands = ()
            circuit._remove_user(user_gate.operands[1 - const_idx], user_gate.label)
        else:
            new_operands = (user_gate.operands[1 - const_idx], )

        return Gate(user_gate.label, new_type, new_operands)

    @staticmethod
    def _simplify_user_gate(circuit: Circuit, user_gate: Gate, const_gate: Gate) -> Gate:
        assert const_gate.gate_type in CONST_GATES
        assert const_gate.label in user_gate.operands, f"{const_gate.label}, {user_gate.operands}"

        if len(user_gate.operands) == 1:
            return RemoveConstantGates._simplify_unary_user_gate(user_gate, const_gate)
        elif len(user_gate.operands) == 2:
            return RemoveConstantGates._simplify_binary_user_gate(circuit, user_gate, const_gate)
        else:
            assert False

    @staticmethod
    def _delete_const_gate(circuit: Circuit, const_label: str) -> None:
        const_gate = circuit.get_gate(const_label)
        for user_label in copy.copy(circuit.get_gate_users(const_label)):
            user_gate = circuit.get_gate(user_label)
            new_user_gate = RemoveConstantGates._simplify_user_gate(circuit, user_gate, const_gate)
            circuit._remove_user(const_label, user_label)
            circuit.gates[user_label] = new_user_gate

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        :param circuit: the original circuit to be simplified
        :return: new simplified version of the circuit

        """
        _new_circuit = copy.copy(circuit)

        while True:
            for gate_label, _gate in _new_circuit.gates.items():
                if _gate.gate_type in CONST_GATES:
                    print(f"TRY Delete gate: {gate_label}")
                    gate_users = _new_circuit.get_gate_users(gate_label)
                    if gate_users:
                        RemoveConstantGates._delete_const_gate(_new_circuit, gate_label)
                        break
            else:
                break

        return _new_circuit
