"""Some circuits validation."""

import typing as tp

import more_itertools

from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitValidationError,
    DeleteBlockError,
    GateHasUsersError,
)


__all__ = [
    'check_gates_exist',
    'check_label_doesnt_exist',
    'check_block_doesnt_exist',
    'check_gate_has_not_users',
    'check_block_has_not_users',
    'check_circuit_has_no_cycles',
]

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Block, Circuit
    from boolean_circuit_tool.core.circuit.gate import Gate, Label


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


def check_gate_has_not_users(gate_label: 'Label', circuit: 'Circuit') -> None:
    """Check that gate hasn't users in the circuit."""
    if len(circuit.get_gate_users(gate_label)) > 0:
        raise GateHasUsersError()


def check_block_doesnt_exist(block_label: 'Label', circuit: 'Circuit') -> None:
    """Check initializations blocks in the circuit."""
    if block_label in circuit.blocks:
        raise CircuitValidationError(
            f'Block {block_label} exists in the circuit',
        )


def check_block_has_not_users(
    block: 'Block',
    circuit: 'Circuit',
    exclusion_gates: tp.Optional[set['Label']] = None,
) -> None:
    """
    Check that gates from block hasn't users in the circuit outside itself.

    :param block: the block for checking
    :param circuit: the circuit
    :param exclusion_gates: gates from the block that are allowed to have users

    """
    if exclusion_gates is None:
        exclusion_gates = set()

    gates_set: set['Label'] = set(block.gates)
    for gate in block.gates:
        if gate not in exclusion_gates:
            for user in circuit.get_gate_users(gate):
                if user not in gates_set:
                    raise DeleteBlockError()


def check_circuit_has_no_cycles(circuit: 'Circuit') -> None:
    """Check that there are no cycles in the circuit."""
    from boolean_circuit_tool.core.circuit.circuit import TraverseState

    def on_discover_hook(
        gate: 'Gate',
        gate_states: tp.Mapping['Label', 'TraverseState'],
    ):
        if gate_states[gate.label] == TraverseState.ENTERED:
            raise CircuitValidationError(
                'Circuit has orinted cycle',
            )

    more_itertools.consume(circuit.dfs(on_discover_hook=on_discover_hook))
