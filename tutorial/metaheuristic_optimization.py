"""
Trivial optimize usage with an existing transformer as a mutation.

Runs MergeDuplicateGates() on the provided circuit once.

"""

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization import (
    SearchConfig,
    TransformerMutation,
    optimize,
    MultiStartRandomWalk,
)
from cirbo.minimization.metaheuristic.instance_frontier import (
    ParetoFrontier,
    CircuitStats,
)
from cirbo.minimization.simplification import MergeDuplicateGates

ckt = Circuit.bare_circuit(2)
ckt.add_gate(Gate('and_1', gate.AND, ('0', '1')))
ckt.add_gate(Gate('and_2', gate.AND, ('0', '1')))
ckt.add_gate(Gate('result', gate.OR, ('and_1', 'and_2')))
ckt.mark_as_output('result')

result = optimize(
    ParetoFrontier(circuits=[ckt]),
    mutations=[TransformerMutation(MergeDuplicateGates())],
    config=SearchConfig(max_stagnation_iterations=1, seed=42, check_equivalence=True),
    search_strategy=MultiStartRandomWalk(1),
)

print(f"Initial: {CircuitStats.from_circuit(ckt)}")
print(result.frontier)
print(result.frontier.get_shallowest())
