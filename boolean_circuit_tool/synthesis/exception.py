"""Module defines exceptions related to synthesis."""

from boolean_circuit_tool.exceptions import BooleanCircuitToolError


class CircuitFinderError(BooleanCircuitToolError):
    """Base for CircuitFinder class exceptions."""

    pass


class TimeOutError(CircuitFinderError):
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
