"""Module defines exceptions related to synthesis."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'CircuitFinderError',
    'SolverTimeOutError',
    'GateIsAbsentError',
    'FixGateError',
    'ForbidWireError',
    'StringTruthTableException',
]


class CircuitFinderError(BooleanCircuitToolError):
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


class ForbidWireError(CircuitFinderError):
    """Error on try to forbid a wire where from_gate >= to_gate."""

    pass


class StringTruthTableException(BooleanCircuitToolError):
    """Every occurrence in the truth table must be '0', '1', or '*'."""

    pass
