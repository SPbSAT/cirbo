"""Subpackage defines plenty of methods for circuits generation and modification of
existing circuits with commonly used gadgets, as well as customisable generation of some
arithmetic circuits."""

from cirbo.synthesis.generation import arithmetics
from cirbo.synthesis.generation.generation import (
    add_if_then_else,
    add_pairwise_if_then_else,
    add_pairwise_xor,
    add_plus_one,
    generate_if_then_else,
    generate_pairwise_if_then_else,
    generate_pairwise_xor,
    generate_plus_one,
)
from cirbo.synthesis.generation.helpers import GenerationBasis


__all__ = [
    'GenerationBasis',
    # Arithmetic subpackage
    'arithmetics',
    # Common generation.
    'generate_plus_one',
    'generate_if_then_else',
    'generate_pairwise_if_then_else',
    'generate_pairwise_xor',
    'add_plus_one',
    'add_if_then_else',
    'add_pairwise_if_then_else',
    'add_pairwise_xor',
]
