"""Module defines exceptions related to minimization."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitMinimizationError',
    'UnsupportedOperationError',
    'FailedValidationError',
]


class CircuitMinimizationError(BooleanCircuitToolError):
    """Base for exceptions related to circuit minimizations."""

    pass


class UnsupportedOperationError(CircuitMinimizationError):
    """Error on unsupported gate operation found in circuit."""

    pass


class FailedValidationError(CircuitMinimizationError):
    """Error on incorrect circuit minimization (circuits are not equivalent)."""

    pass
