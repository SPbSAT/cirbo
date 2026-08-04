"""Trivial optimize usage with an existing transformer as a mutation."""

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization import SearchConfig, TransformerMutation, optimize
from cirbo.minimization.simplification import MergeDuplicateGates

circuit = Circuit.bare_circuit(2)
circuit.add_gate(Gate('and_1', gate.AND, ('0', '1')))
circuit.add_gate(Gate('and_2', gate.AND, ('0', '1')))
circuit.add_gate(Gate('result', gate.OR, ('and_1', 'and_2')))
circuit.mark_as_output('result')

result = optimize(
    circuit,
    mutations=[TransformerMutation(MergeDuplicateGates())],
    config=SearchConfig(max_iterations=10, seed=42),
)

print(result.initial_metrics)
print(result.best_metrics)
print(result.termination_reason)
