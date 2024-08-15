"""Module defines base Protocol for any class which purpose is to simplify a circuit
(reduce number of gates in it)."""

import typing as tp

from boolean_circuit_tool.core import Circuit


__all__ = [
    'CircuitSimplifier',
]


class CircuitSimplifier(tp.Protocol):
    """
    Protocol for any object that behaves like circuit simplifier.

    Allows simplifier to define:
    1. Pre-requisites (e.g. which simplifiers must be executed before this one)
    2. Post-requisites (e.g.  which simplifiers must be executed after this one)

    """

    def simplify(self, circuit: Circuit) -> Circuit:
        """
        Performs simplification of the given `circuit`. Will return new `Circuit`.

        :return: new circuit object.

        """

    def get_pre_requisites(self) -> tp.Sequence['CircuitSimplifier']:
        """
        Returns list of pre-requisite simplification steps which must be completed
        before this one is performed.

        :return: new circuit object.

        """

    def get_post_requisites(self) -> tp.Sequence['CircuitSimplifier']:
        """
        Returns list of post-requisite simplification steps which must be completed
        before this one is performed.

        :return: new circuit object.

        """
