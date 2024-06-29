"""Some circuits validation."""

import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import GateLabel

__all__ = ['check_gates_exist', 'check_gate_lable_doesnt_exist']

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Circuit


def check_gates_exist(gates: tuple[GateLabel, ...], circuit: 'Circuit') -> None:
    """Checks that provided gates are it the circuit."""
    for gate in gates:
        if gate not in circuit.gates.keys():
            raise CircuitValidationError(
                f'Operand {gate} are not initialized in the circuit',
            )


def check_gate_lable_doesnt_exist(gate_label: GateLabel, circuit: 'Circuit') -> None:
    """Check initializations operands into the circuit."""
    if gate_label in circuit.gates.keys():
        raise CircuitValidationError(
            f'Gate {gate_label} exists in the circuit',
        )
