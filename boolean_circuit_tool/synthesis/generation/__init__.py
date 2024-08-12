"""Subpackage defines plenty of methods for circuits generation and modification of
existing circuits with commonly used gadgets, as well as customisable generation of some
arithmetic circuits."""

from boolean_circuit_tool.synthesis.generation import arithmetics
from boolean_circuit_tool.synthesis.generation.generation import (
    add_if_then_else,
    add_pairwise_if_then_else,
    add_pairwise_xor,
    add_plus_one,
    generate_if_then_else,
    generate_inputs,
    generate_inputs_with_labels,
    generate_pairwise_if_then_else,
    generate_pairwise_xor,
    generate_plus_one,
)


__all__ = [
    # Arithmetic subpackage
    'arithmetics',
    # Common generation.
    'generate_plus_one',
    'generate_if_then_else',
    'generate_pairwise_if_then_else',
    'generate_pairwise_xor',
    'generate_inputs_with_labels',
    'generate_inputs',
    'add_plus_one',
    'add_if_then_else',
    'add_pairwise_if_then_else',
    'add_pairwise_xor',
]
