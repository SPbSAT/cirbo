"""Subpackage containes plenty of circuit minimization algorithms including low effort
simplification algorithms located in pacakge `simplification` and represented in as a
composition in the method `cleanup` and subcircuit minimization algorithm defined by
`minimize_subcircuits` method."""

from .metaheuristic import (
    ABC_EASY_COMMANDS,
    ABC_HARD_COMMANDS,
    ABCEasyMutation,
    ABCHardMutation,
    CircuitMetrics,
    CircuitMutation,
    measure_circuit,
    optimize,
    ParetoRandomRestartHillClimber,
    SearchConfig,
    SearchResult,
    SearchStrategy,
    TransformerMutation,
)
from .simplification import cleanup, MergeUnaryOperators, RemoveRedundantGates
from .subcircuit import minimize_subcircuits

__all__ = [
    # simplification.py
    'RemoveRedundantGates',
    'MergeUnaryOperators',
    'cleanup',
    # subcircuit.py
    'minimize_subcircuits',
    # metaheuristic
    'CircuitMetrics',
    'ABC_EASY_COMMANDS',
    'ABC_HARD_COMMANDS',
    'ABCEasyMutation',
    'ABCHardMutation',
    'measure_circuit',
    'SearchConfig',
    'SearchResult',
    'SearchStrategy',
    'ParetoRandomRestartHillClimber',
    'optimize',
    'CircuitMutation',
    'TransformerMutation',
]
