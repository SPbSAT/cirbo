"""
Trivial optimize usage with an existing transformer as a mutation.

Runs MergeDuplicateGates() on the provided circuit once.

"""

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization import SearchConfig, TransformerMutation, optimize
from cirbo.minimization.metaheuristic.instance_frontier import (
    InstanceParetoFrontier,
    CircuitMetrics,
)
from cirbo.minimization.simplification import MergeDuplicateGates

ckt = Circuit.bare_circuit(2)
ckt.add_gate(Gate('and_1', gate.AND, ('0', '1')))
ckt.add_gate(Gate('and_2', gate.AND, ('0', '1')))
ckt.add_gate(Gate('result', gate.OR, ('and_1', 'and_2')))
ckt.mark_as_output('result')
initial_metrics = CircuitMetrics.from_circuit(ckt)

result = optimize(
    InstanceParetoFrontier(circuits=[ckt]),
    mutations=[TransformerMutation(MergeDuplicateGates())],
    config=SearchConfig(max_iterations=1, seed=42, check_equivalence=True),
)

print(len(result.frontier))
print(initial_metrics)
print(result.frontier.get_frontier()[0].metrics)
print(result.termination_reason)
