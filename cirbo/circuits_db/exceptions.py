from cirbo.exceptions import CirboError

__all__ = [
    'BinaryDictIOError',
    'BitIOError',
    'CircuitsDatabaseError',
    'CircuitDatabaseOpenError',
    'CircuitDatabaseCloseError',
    'CircuitDatabaseNotOpenedError',
    'NormalizationError',
    'NormalizationParametersError',
    'NormalizationParametersAreNotInitialized',
    'CircuitIsNotCompatibleWithNormalizationParameters',
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


class NormalizationError(CircuitsDatabaseError):
    pass


class NormalizationParametersError(NormalizationError):
    pass


class CircuitIsNotCompatibleWithNormalizationParameters(NormalizationParametersError):
    pass


class NormalizationParametersAreNotInitialized(NormalizationParametersError):
    pass
