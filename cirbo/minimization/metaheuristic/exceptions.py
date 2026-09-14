"""Exceptions raised by metaheuristic circuit optimization."""

from cirbo.minimization.exception import CircuitMinimizationError

__all__ = ['MetaheuristicError', 'InvalidSearchConfigError', 'InvalidFrontierError']


class MetaheuristicError(CircuitMinimizationError):
    """Base exception for metaheuristic optimisation."""


class InvalidSearchConfigError(MetaheuristicError):
    """Raised when a search has no finite stopping condition."""


class InvalidFrontierError(MetaheuristicError):
    """Raised when an instance frontier cannot be searched safely."""
