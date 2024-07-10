"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitError',
    'CircuitValidationError',
    'CircuitElementIsAbsentError',
    'CircuitElementAlreadyExistsError',
    'GateTypeNoOperatorError',
    'GateStateError',
]


class CircuitError(BooleanCircuitToolError):
    """Base for Circuit class exceptions."""

    pass


class CircuitValidationError(CircuitError):
    """Represents error of circuit validation, e.g. circuit mutation that led to invalid
    state."""

    pass


class CircuitElementIsAbsentError(CircuitError):
    """Error on try to access absent element."""

    pass


class CircuitElementAlreadyExistsError(CircuitError):
    """Error on creation of element that already exists."""

    pass


class GateTypeNoOperatorError(CircuitError):
    """Represents error in operator getter, when operator is None."""

    pass


class GateStateError(CircuitError):
    """Represents error of gate state."""

    pass
