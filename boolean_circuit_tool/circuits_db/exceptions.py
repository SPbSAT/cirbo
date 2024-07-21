from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'BinaryDictIOError',
    'BitIOError',
    'CircuitsDatabaseError',
]


class CircuitsDatabaseError(BooleanCircuitToolError):
    pass


class BinaryDictIOError(CircuitsDatabaseError):
    pass


class BitIOError(CircuitsDatabaseError):
    pass


class CircuitCodingError(CircuitsDatabaseError):
    pass
