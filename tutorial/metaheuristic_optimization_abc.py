"""Use optional ABC mutations in the metaheuristic circuit optimizer."""

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization import (
    ABCHardMutation,
    SearchConfig,
    optimize,
    InstanceParetoFrontier,
    CircuitMetrics,
)

ckt = Circuit.bare_circuit(3)
ckt.add_gate(Gate('and_1', gate.AND, ('0', '1')))
ckt.add_gate(Gate('and_2', gate.AND, ('0', '1')))
ckt.add_gate(Gate('result', gate.OR, ('and_1', 'and_2')))
ckt.mark_as_output('result')
initial_metrics = CircuitMetrics.from_circuit(ckt)

# Requires a build with the optional abc_wrapper extension enabled.
result = optimize(
    InstanceParetoFrontier(circuits=[ckt]),
    mutations=[ABCHardMutation()],
    config=SearchConfig(max_iterations=100, seed=42),
)

print(len(result.frontier))
print(initial_metrics)
print(result.frontier.get_frontier()[0].metrics)
