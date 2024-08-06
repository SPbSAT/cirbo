"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitError',
    'CircuitValidationError',
    'CircuitGateIsAbsentError',
    'CircuitGateAlreadyExistsError',
    'GateTypeNoOperatorError',
    'GateStateError',
    'TraverseMethodError',
    'CreateBlockError',
]


class CircuitError(BooleanCircuitToolError):
    """Base for Circuit class exceptions."""

    pass


class CircuitValidationError(CircuitError):
    """Represents error of circuit validation, e.g. circuit mutation that led to invalid
    state."""

    pass


class CircuitGateIsAbsentError(CircuitError):
    """Error on try to access absent gate."""

    pass


class CircuitGateAlreadyExistsError(CircuitError):
    """Error on creation of gate that already exists."""

    pass


class CircuitIsCyclicalError(CircuitError):
    """Error the circuit has a cycle."""

    pass


class GateTypeNoOperatorError(CircuitError):
    """Represents error in operator getter, when operator is None."""

    pass


class GateStateError(CircuitError):
    """Represents error of gate state."""

    pass


class TraverseMethodError(CircuitError):
    """Represents error of method for traverse circuit."""

    pass


class CreateBlockError(CircuitError):
    """Represents error in creating block in the circuit."""

    pass
