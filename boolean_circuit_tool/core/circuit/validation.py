"""Some circuits validation."""

import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError

__all__ = ['check_elements_exist', 'check_label_doesnt_exist']

if tp.TYPE_CHECKING:
    from boolean_circuit_tool.core.circuit.circuit import Circuit
    from boolean_circuit_tool.core.circuit.gate import Label


def check_elements_exist(elements: tuple['Label', ...], circuit: 'Circuit') -> None:
    """Checks that provided gates are it the circuit."""
    for element in elements:
        if element not in circuit._elements:
            raise CircuitValidationError(
                f'Operand {element} are not initialized in the circuit',
            )


def check_label_doesnt_exist(label: 'Label', circuit: 'Circuit') -> None:
    """Check initializations operands into the circuit."""
    if label in circuit._elements:
        raise CircuitValidationError(
            f'Gate {label} exists in the circuit',
        )
