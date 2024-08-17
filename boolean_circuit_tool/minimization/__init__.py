"""Subpackage containes plenty of circuit minimization algorithms including low effort
simplification algorithms located in pacakge `simplification` and represented in as a
composition in the method `cleanup` and subcircuit minimization algorithm defined by
`minimize_subcircuits` method."""

from .simplification import cleanup, CollapseUnaryOperators, RemoveRedundantGates
from .subcircuit import minimize_subcircuits

__all__ = [
    # simplification.py
    'RemoveRedundantGates',
    'CollapseUnaryOperators',
    'cleanup',
    # subcircuit.py
    'minimize_subcircuits',
]
