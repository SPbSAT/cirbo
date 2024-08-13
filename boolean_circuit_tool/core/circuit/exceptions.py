"""Module defines exceptions related to core objects, e.g. Circuit."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitError',
    'CircuitValidationError',
    'CircuitGateIsAbsentError',
    'CircuitGateAlreadyExistsError',
    'CircuitIsCyclicalError',
    'GateTypeNoOperatorError',
    'GateStateError',
    'GateHasUsersError',
    'GateNotInputError',
    'GateDoesntExistError',
    'TraverseMethodError',
    'CreateBlockError',
    'DeleteBlockError',
    'OverlappingBlocksError',
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


class GateHasUsersError(CircuitError):
    """Represents error that gate has users, this gate can't be deleted."""

    pass


class GateNotInputError(CircuitError):
    """Represents error that gate is not input, this gate's type can't be changed."""

    pass


class GateDoesntExistError(CircuitError):
    """Represents error that gate doesn't exist, and you can not receive the information
    about it."""

    pass


class TraverseMethodError(CircuitError):
    """Represents error of method for traverse circuit."""

    pass


class CreateBlockError(CircuitError):
    """Represents error in creating block in the circuit."""

    pass


class DeleteBlockError(CircuitError):
    """Represents error in deleting block in the circuit."""

    pass


class OverlappingBlocksError(CircuitError):
    """Represents error that circuit has overlapping blocks."""

    pass
