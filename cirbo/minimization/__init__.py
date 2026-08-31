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
    InstanceDescriptor,
    InstanceFrontier,
    InstanceParetoFrontier,
    InvalidFrontierError,
    optimize,
    ParetoRandomRestartHillClimber,
    SearchConfig,
    SearchResult,
    SearchStrategy,
    TerminationReason,
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
    'ABC_EASY_COMMANDS',
    'ABC_HARD_COMMANDS',
    'ABCEasyMutation',
    'ABCHardMutation',
    'SearchConfig',
    'SearchResult',
    'SearchStrategy',
    'TerminationReason',
    'ParetoRandomRestartHillClimber',
    'optimize',
    'CircuitMutation',
    'TransformerMutation',
    'CircuitMetrics',
    'InstanceDescriptor',
    'InstanceFrontier',
    'InstanceParetoFrontier',
    'InvalidFrontierError',
]
