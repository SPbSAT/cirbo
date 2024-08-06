"""Some circuits validation."""

import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError


__all__ = ['check_gates_exist', 'check_label_doesnt_exist', 'check_block_doesnt_exist']

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Circuit
    from boolean_circuit_tool.core.circuit.gate import Label


def check_gates_exist(gates: tp.Sequence['Label'], circuit: 'Circuit') -> None:
    """Checks that provided gates are it the circuit."""
    for gate_label in gates:
        if not circuit.has_gate(gate_label):
            raise CircuitValidationError(
                f'Gate {gate_label} are not initialized in the circuit',
            )


def check_label_doesnt_exist(gate_label: 'Label', circuit: 'Circuit') -> None:
    """Check initializations gates in the circuit."""
    if circuit.has_gate(gate_label):
        raise CircuitValidationError(
            f'Gate {gate_label} has already existed in the circuit',
        )
    
    
def check_block_doesnt_exist(block_label: 'Label', blocks: list[Label]) -> None:
    """Check initializations blocks in the circuit."""
    if block_label in blocks:
        raise CircuitValidationError(
            f'Block {block_label} has already existed in the circuit',
        )

