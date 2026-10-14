from cirbo.exceptions import CirboError

__all__ = [
    'BinaryDictIOError',
    'BitIOError',
    'CircuitsDatabaseError',
    'CircuitDatabaseOpenError',
    'CircuitDatabaseCloseError',
    'CircuitDatabaseNotOpenedError',
    'CircuitEncodingError',
]


class CircuitsDatabaseError(CirboError):
    pass


class CircuitDatabaseOpenError(CircuitsDatabaseError):
    pass


class CircuitDatabaseCloseError(CircuitsDatabaseError):
    pass


class CircuitDatabaseNotOpenedError(CircuitsDatabaseError):
    pass


class BinaryDictIOError(CircuitsDatabaseError):
    pass


class BitIOError(CircuitsDatabaseError):
    pass


class CircuitEncodingError(CircuitsDatabaseError):
    pass
