"""Some circuits validation."""

import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitValidationError,
    DeleteBlockError,
    GateHasUsersError,
)


__all__ = [
    'check_gates_exist',
    'check_label_doesnt_exist',
    'check_block_doesnt_exist',
    'check_gate_hasnt_users',
    'check_block_hasnt_users',
]

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Block, Circuit
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
            f'Gate {gate_label} exists in the circuit',
        )


def check_gate_hasnt_users(gate_label: 'Label', circuit: 'Circuit') -> None:
    """Check that gate hasn't users in the circuit."""
    if len(circuit.get_gate_users(gate_label)) > 0:
        raise GateHasUsersError()


def check_block_doesnt_exist(block_label: 'Label', circuit: 'Circuit') -> None:
    """Check initializations blocks in the circuit."""
    if block_label in circuit.blocks:
        raise CircuitValidationError(
            f'Block {block_label} exists in the circuit',
        )


def check_block_hasnt_users(block: 'Block', circuit: 'Circuit') -> None:
    """Check that block hasn't users in the circuit outside itself."""
    gates_set: set[Label] = set(block.gates)
    for gate in block.gates:
        for user in circuit.get_gate_users(gate):
            if user not in gates_set:
                raise DeleteBlockError()
