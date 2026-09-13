"""Use optional ABC mutations in the metaheuristic circuit optimizer."""

from cirbo.minimization import (
    ABCHeavyMutation,
    SearchConfig,
    optimize,
    MultiStartRandomWalk,
    CircuitStats,
)
from cirbo.synthesis.generation.arithmetics import generate_sum_n_bits

ckt = generate_sum_n_bits(n=7, basis='AIG')
initial_stats = CircuitStats.from_circuit(ckt)

# Requires a build with the optional abc_wrapper extension enabled.
result = optimize(
    ckt,
    ABCHeavyMutation(),
    SearchConfig(20, 3, check_equivalence=True, seed=42),
    search_strategy=MultiStartRandomWalk(100),
)

print(f"Initial: {initial_stats}")
print(f"Result: {result.frontier}")
