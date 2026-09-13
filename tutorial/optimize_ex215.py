"""
Examples uses ABC mutations in the metaheuristic circuit optimizer
to improve pareto frontier of the ex215 IWLS 2026 benchmark.
"""

import logging
from pathlib import Path

from cirbo.circuits_db.data_utils import resolve_default_data_path
from cirbo.minimization import (
    ParetoFrontier,
    optimize,
    SearchConfig,
    MultiStartRandomWalk,
)
from cirbo.minimization.metaheuristic.abc import ABCHeavyMutation

logging.basicConfig(level=logging.INFO)

ex215_dir = resolve_default_data_path('ex215_frontier')
ex215_initial_frontier = ParetoFrontier.read_dir(ex215_dir)

# Requires a build with the optional abc_wrapper extension enabled.
res = optimize(
    ex215_initial_frontier,
    ABCHeavyMutation(),
    SearchConfig(1, 3, seed=42),
    search_strategy=MultiStartRandomWalk(1),
)

print(res)
print(res.frontier)
print(f"Initial frontier size: {len(ex215_initial_frontier)}")
print(f"Resulting frontier size: {len(res.frontier)}")

result_dir = Path("ex215_optimized_frontier")
res.frontier.write_dir(result_dir, prefix="ex215", remove_existing=True)
