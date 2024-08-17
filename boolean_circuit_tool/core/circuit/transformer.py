"""
Module defines base Transformer Protocol for any class which purpose is to transform a
circuit.

Transformers do not change a circuit itself, but create a transformed copy of it, which
possesses some new qualities (e.g. has no redundant gates).

"""

import abc
import copy
import functools
import logging
import typing as tp

from boolean_circuit_tool.core.circuit import Circuit


__all__ = [
    'Transformer',
    'TransformerComposition',
]


logger = logging.getLogger(__name__)


class Transformer(metaclass=abc.ABCMeta):
    """
    Base for any object that performs circuit transformation (e.g. circuit
    simplification).

    Transformer is an independent and self-sufficient battery.

    Note: one can specify pre- and post-transformers required by this transformer
    in the super call of `__init__` method.

    """

    __idempotent__: bool = False

    @staticmethod
    def linearize_transformers(
        transformers: tp.Union[tp.Iterable['Transformer'], 'TransformerComposition'],
    ) -> tp.Iterable['Transformer']:
        """
        Prepares iterator over `Transformer` objects originally given either as a
        separate `Transformer` or as a `TransformerComposition`.

        :param transformers: iterable over either transformers or their compositions
        :return: flatten list of `Transformers`.

        """
        for t in transformers:
            yield from t.as_distinct(imply_deps=True)

    @staticmethod
    def linearize_reduce_transformers(
        transformers: tp.Union[tp.Iterable['Transformer'], 'TransformerComposition'],
    ) -> tp.Iterable['Transformer']:
        """
        Prepares iterator over `Transformer` objects originally given either as a
        separate `Transformer` or as a `TransformerComposition` and reduced consequent
        idempotent transformers.

        :param transformers: iterable over either transformers or their compositions
        :return: flatten list of `Transformers` where consequent idempotent transformers are reduced.

        """
        _prev: tp.Optional[Transformer] = None
        for _cur in Transformer.linearize_transformers(transformers):
            # skip transformer if it was already applied right before this one.
            if _cur.is_idempotent and _cur == _prev:
                continue

            yield _cur
            _prev = _cur

    @staticmethod
    def apply_transformers(
        circuit: Circuit,
        transformers: tp.Union[tp.Iterable['Transformer'], 'TransformerComposition'],
    ) -> Circuit:
        """
        Applies several transformations consecutively to the provided circuit.

        :param circuit: the original circuit to be simplified
        :param transformers: Transformer objects which must be applied to a circuit.
        :return: new transformed version of the circuit

        """
        _transformers: tp.Iterable[Transformer]
        if isinstance(transformers, TransformerComposition):
            _transformers = [transformers]
        else:
            _transformers = transformers

        # apply transformers to the circuit.
        return functools.reduce(
            lambda _circ, _transformer: _transformer._transform(_circ),
            Transformer.linearize_reduce_transformers(_transformers),
            circuit,
        )

    def __init__(
        self,
        pre_transformers: tp.Sequence['Transformer'] = tuple(),
        post_transformers: tp.Sequence['Transformer'] = tuple(),
    ):
        self._post_transformers = post_transformers
        self._pre_transformers = pre_transformers

    @abc.abstractmethod
    def _transform(self, circuit: Circuit) -> Circuit:
        """
        Defines main transformation of `self`. It should not be used standalone (and so
        is made protected) because is designed to rely on the execution of pre- and
        post-transformers specified in `__init__`.

        To apply transformation with pre- and post-conditions see `transform` method.

        Must return new `Circuit`.

        :return: new circuit object.

        """
        raise NotImplementedError()

    @property
    def is_idempotent(self) -> bool:
        """
        Returns True iff this transformer is idempotent, meaning that its consequent
        application will have no effect on resulting circuit.

        :return: True iff this transformer is idempotent.

        """
        return self.__idempotent__

    @property
    def pre_transformers(self) -> tp.Sequence['Transformer']:
        """
        :return: list of transformers, which must be applied before this one.

        """
        return self._pre_transformers

    @property
    def post_transformers(self) -> tp.Sequence['Transformer']:
        """
        :return: list of transformers, which must be applied after this one.

        """
        return self._post_transformers

    def transform(self, circuit: Circuit) -> Circuit:
        """
        Performs a transformation of the given `circuit`, return new `Circuit`.

        Must return new `Circuit`.

        :return: new circuit object.

        """
        return self.apply_transformers(circuit, [self])

    def as_distinct(self, *, imply_deps: bool = True) -> tp.Iterable['Transformer']:
        """
        :param imply_deps: If True, then will return pre- and post-transformers as well.
        :return: iterator over underlying `Transformer` objects. Suitable for
        implementation of transformer composition.

        """
        if imply_deps:
            yield from self.linearize_transformers(self._pre_transformers)
        yield self
        if imply_deps:
            yield from self.linearize_transformers(self._post_transformers)

    def __eq__(self, other: tp.Any):
        if not isinstance(other, Transformer):
            return NotImplemented
        # By default, only types are compared. It affects reduction of idempotent
        # transformers. This behaviour may be redefined in successors.
        return type(self) == type(other)

    def __or__(self, other: tp.Any) -> 'TransformerComposition':
        """Convenient operator for composing (piping) transformers."""
        if isinstance(other, TransformerComposition):
            return TransformerComposition(list(self.as_distinct()) + other.transformers)

        if isinstance(other, Transformer):
            return TransformerComposition(list(self.as_distinct()) + [other])

        return NotImplemented

    def __ror__(self, other: tp.Any) -> 'TransformerComposition':
        """Convenient operator for composing (piping) transformers."""
        if isinstance(other, TransformerComposition):
            return TransformerComposition(other.transformers + list(self.as_distinct()))

        if isinstance(other, Transformer):
            return TransformerComposition([other] + list(self.as_distinct()))

        return NotImplemented


class TransformerComposition(Transformer):
    """Base for any object that represents a sequence of circuit transformations."""

    def __init__(self, transformers: tp.Sequence[Transformer]):
        # no pre- or post-transformers required.
        super().__init__()
        self._transformers = list(transformers)

    @property
    def transformers(self) -> tp.List[Transformer]:
        """
        :return: copy of underlying transformers list
        """
        return copy.copy(self._transformers)

    def _transform(self, circuit: Circuit) -> Circuit:
        """
        Applies all underlying transformers to the given `circuit`, return new
        `Circuit`.

        :return: new circuit object.

        """
        return Transformer.apply_transformers(circuit, self)

    def as_distinct(self, *, imply_deps: bool = True) -> tp.Iterable['Transformer']:
        """
        :param imply_deps: If True, then will return pre- and post-transformers as well.
        :return: iterator over underlying `Transformer` objects. Suitable for
        implementation of transformer composition.

        """
        yield from Transformer.linearize_transformers(self._transformers)

    def __eq__(self, other: tp.Any):
        if not isinstance(other, Transformer):
            return NotImplemented

        # Always returns False.
        #
        # May be changed for smarter idempotent sequence reduction in the future.
        return False
