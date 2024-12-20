"""Module defines exceptions related to synthesis."""

from cirbo.exceptions import CirboError

__all__ = [
    'CircuitFinderError',
    'SolverTimeOutError',
    'GateIsAbsentError',
    'FixGateError',
    'ForbidWireOrderError',
    'StringTruthTableError',
    'NoSolutionError',
    'FixGateOrderError',
]


class CircuitFinderError(CirboError):
    """Base for CircuitFinder class exceptions."""

    pass


class SolverTimeOutError(CircuitFinderError):
    """Error is due to the time limit of the solver."""

    pass


class GateIsAbsentError(CircuitFinderError):
    """Error on try to access absent gate."""

    pass


class FixGateError(CircuitFinderError):
    """Error on try to fix gate without specifying any predecessor."""

    pass


class FixGateOrderError(CircuitFinderError):
    """Error on try to fix gate with wrong order of predecessor."""

    pass


class ForbidWireOrderError(CircuitFinderError):
    """Error on try to forbid a wire where from_gate >= to_gate."""

    pass


class StringTruthTableError(CirboError):
    """Every occurrence in the truth table must be '0', '1', or '*'."""

    pass


class NoSolutionError(CircuitFinderError):
    """Raised when no solution is found."""

    pass
