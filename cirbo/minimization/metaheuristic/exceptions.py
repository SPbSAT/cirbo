"""Exceptions raised by metaheuristic circuit optimization."""

from cirbo.minimization.exception import CircuitMinimizationError

__all__ = [
    'MetaheuristicError',
    'InvalidSearchConfigError',
    'ABCUnavailableError',
]


class MetaheuristicError(CircuitMinimizationError):
    """Base exception for metaheuristic optimisation."""


class InvalidSearchConfigError(MetaheuristicError):
    """Raised when a search has no finite stopping condition."""


class ABCUnavailableError(MetaheuristicError):
    """Raised when an ABC mutation is used without the native ABC extension."""
