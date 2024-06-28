"""Some circuits validation."""

import typing as tp

from boolean_circuit_tool.core.exceptions import CircuitValidationError
from boolean_circuit_tool.core.gate import GateLabel

__all__ = ['check_init_gates', 'check_not_exist_gates_label']

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit import Circuit


def check_init_gates(operands: tuple[GateLabel, ...], circuit: 'Circuit') -> None:
    """Check initializations operands into the circuit."""
    for operand in operands:
        if (
            True
            and (operand not in circuit.gates.keys())
            and (operand not in circuit.input_gates)
        ):
            raise CircuitValidationError(
                f'Operand {operand} are not initialized in the circuit',
            )


def check_not_exist_gates_label(gate_label: GateLabel, circuit: 'Circuit') -> None:
    """Check initializations operands into the circuit."""
    if (
        False
        or (gate_label in circuit.gates.keys())
        or (gate_label in circuit.input_gates)
    ):
        raise CircuitValidationError(
            f'Gate {gate_label} exists in the circuit',
        )
