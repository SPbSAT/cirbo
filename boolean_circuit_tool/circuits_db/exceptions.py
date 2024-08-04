from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = [
    'BinaryDictIOError',
    'BitIOError',
    'CircuitsDatabaseError',
    'CircuitDatabaseOpenError',
    'CircuitDatabaseCloseError'
]


class CircuitsDatabaseError(BooleanCircuitToolError):
    pass


class CircuitDatabaseOpenError(CircuitsDatabaseError):
    pass


class CircuitDatabaseCloseError(CircuitsDatabaseError):
    pass


class BinaryDictIOError(CircuitsDatabaseError):
    pass


class BitIOError(CircuitsDatabaseError):
    pass


class CircuitCodingError(CircuitsDatabaseError):
    pass
