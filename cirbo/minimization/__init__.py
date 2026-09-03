"""Subpackage containes plenty of circuit minimization algorithms including low effort
simplification algorithms located in pacakge `simplification` and represented in as a
composition in the method `cleanup` and subcircuit minimization algorithm defined by
`minimize_subcircuits` method."""

from .metaheuristic import (
    ABC_HEAVY_COMMANDS,
    ABC_LIGHT_COMMANDS,
    ABCHeavyMutation,
    ABCLightMutation,
    CircuitMetrics,
    CircuitMutation,
    InstanceDescriptor,
    InstanceFrontier,
    InvalidFrontierError,
    MultiStartRandomWalk,
    optimize,
    ParetoFrontier,
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
    'ABC_LIGHT_COMMANDS',
    'ABC_HEAVY_COMMANDS',
    'ABCLightMutation',
    'ABCHeavyMutation',
    'SearchConfig',
    'SearchResult',
    'SearchStrategy',
    'TerminationReason',
    'MultiStartRandomWalk',
    'optimize',
    'CircuitMutation',
    'TransformerMutation',
    'CircuitMetrics',
    'InstanceDescriptor',
    'InstanceFrontier',
    'ParetoFrontier',
    'InvalidFrontierError',
]
