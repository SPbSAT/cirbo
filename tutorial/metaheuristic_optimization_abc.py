"""Use optional ABC mutations in the metaheuristic circuit optimizer."""

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization import ABCHardMutation, SearchConfig, optimize

circuit = Circuit.bare_circuit(3)
circuit.add_gate(Gate('and_01', gate.AND, ('0', '1')))
circuit.add_gate(Gate('result', gate.AND, ('and_01', '2')))
circuit.mark_as_output('result')

# Requires a build with the optional abc_wrapper extension enabled.
result = optimize(
    circuit,
    mutations=[ABCHardMutation()],
    config=SearchConfig(max_iterations=100, seed=42),
)

print(result.initial_metrics)
print(result.best_metrics)
