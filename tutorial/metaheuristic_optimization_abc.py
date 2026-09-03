"""Use optional ABC mutations in the metaheuristic circuit optimizer."""

import pprint

from cirbo.core import Circuit
from cirbo.minimization import (
    ABCHeavyMutation,
    SearchConfig,
    optimize,
    CircuitMetrics,
    MultiStartRandomWalk,
)
from cirbo.synthesis.generation.arithmetics import add_sum_n_bits

ckt = Circuit.bare_circuit(input_size=7)
*_, b2 = add_sum_n_bits(ckt, ckt.inputs, basis='AIG')
ckt.mark_as_output(b2)

initial_metrics = CircuitMetrics.from_circuit(ckt)

# Requires a build with the optional abc_wrapper extension enabled.
result = optimize(
    ckt,
    ABCHeavyMutation(),
    SearchConfig(1, seed=42),
    search_strategy=MultiStartRandomWalk(100),
)

pprint.pp(result)
print(initial_metrics)
print(result.frontier)
print(result.termination_reason)
