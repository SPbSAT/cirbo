"""Module defines auxiliary objects helpful when building an API of generation
methods."""

import enum

__all__ = [
    'GenerationBasis',
]


class GenerationBasis(enum.Enum):
    """Represents basis which is need to be used for generation."""

    # Basis that can contain only gates which can be encoded in XAIG format.
    XAIG = "XAIG"
    # Basis that can contain only gates which can be encoded in AIG format.
    AIG = "AIG"
