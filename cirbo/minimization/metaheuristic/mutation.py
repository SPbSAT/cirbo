"""Function-preserving circuit mutations used by metaheuristic searches."""

import abc
import random
import typing as tp

from cirbo.core.circuit import Circuit
from cirbo.core.circuit.transformer import Transformer

__all__ = [
    'CircuitMutation',
    'TransformerMutation',
]


class CircuitMutation(metaclass=abc.ABCMeta):
    """Base class for a random, function-preserving circuit transformation."""

    @abc.abstractmethod
    def mutate(self, circuit: Circuit, rng: random.Random) -> tp.Optional[Circuit]:
        """Return a mutated copy of ``circuit``, or ``None`` when not applicable."""
        raise NotImplementedError()


class TransformerMutation(CircuitMutation):
    """Adapts an existing :class:`Transformer` to the mutation interface."""

    def __init__(self, transformer: Transformer):
        self._transformer = transformer

    def mutate(self, circuit: Circuit, rng: random.Random) -> tp.Optional[Circuit]:
        """Apply the wrapped transformer. ``rng`` is accepted for uniformity."""
        del rng
        return self._transformer.transform(circuit)
