"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitError',
    'CircuitValidationError',
    'GateStateError',
]


class CircuitError(BooleanCircuitToolError):
    """Base for Circuit class exceptions."""

    pass


class CircuitValidationError(CircuitError):
    """Represents error of circuit validation, e.g. circuit mutation that led to invalid
    state."""

    pass


class GateStateError(BooleanCircuitToolError):
    """Represents error of gate state."""

    pass
