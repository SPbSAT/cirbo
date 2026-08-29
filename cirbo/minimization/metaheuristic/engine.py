"""Extensible metaheuristic search for Boolean circuits."""

import abc
import dataclasses
import enum
import random
import time
import typing as tp

from cirbo.core.circuit import Circuit
from cirbo.sat.sat import check_circuits_equivalence
from .exceptions import InvalidSearchConfigError
from .mutation import CircuitMutation

__all__ = [
    'CircuitMetrics',
    'SearchConfig',
    'SearchResult',
    'TerminationReason',
    'SearchStrategy',
    'ParetoHillClimber',
    'measure_circuit',
    'optimize',
]


@dataclasses.dataclass(frozen=True, order=True)
class CircuitMetrics:
    """Objective values used by the built-in Pareto search."""

    size: int
    depth: int


def measure_circuit(circuit: Circuit) -> CircuitMetrics:
    """Measure gate count and the longest non-input gate path to an output."""
    return CircuitMetrics(size=circuit.size, depth=circuit.get_depth())


def _dominates(left: CircuitMetrics, right: CircuitMetrics) -> bool:
    return left.size <= right.size and left.depth <= right.depth and left != right


@dataclasses.dataclass(frozen=True)
class SearchConfig:
    """Bounded-run and candidate-validation settings for a search."""

    max_iterations: tp.Optional[int] = None
    time_limit_sec: tp.Optional[float] = None
    seed: tp.Optional[int] = None
    mutation_weights: tp.Optional[tp.Sequence[float]] = None

    def __post_init__(self) -> None:
        if self.max_iterations is None and self.time_limit_sec is None:
            raise InvalidSearchConfigError(
                'Either max_iterations or time_limit_sec must be specified.'
            )

        if self.max_iterations is not None and self.max_iterations < 0:
            raise InvalidSearchConfigError('max_iterations must be non-negative.')

        if self.time_limit_sec is not None and self.time_limit_sec < 0:
            raise InvalidSearchConfigError('time_limit_sec must be non-negative.')

        if self.mutation_weights is not None and any(
            weight <= 0 for weight in self.mutation_weights
        ):
            raise InvalidSearchConfigError('mutation weights must be positive.')

    def choose_random_mutation(
        self,
        rng: random.Random,
        mutations: tp.Sequence[CircuitMutation],
    ) -> CircuitMutation:
        """
        Chooses random mutation according to this config.
        Uses weighted probabilities if weights are specified.
        """
        if self.mutation_weights is None:
            return rng.choice(mutations)
        else:
            return rng.choices(mutations, weights=self.mutation_weights, k=1)[0]


class TerminationReason(enum.Enum):
    """Reasons for search termination."""

    ITERATION_LIMIT = 'iteration_limit'
    TIME_LIMIT = 'time_limit'
    NO_MUTATIONS = 'no_mutations'


@dataclasses.dataclass(frozen=True)
class SearchResult:
    """Result and accounting data produced by a search strategy."""

    frontier: tuple[tuple[Circuit, CircuitMetrics], ...]
    best: Circuit
    initial_metrics: CircuitMetrics
    best_metrics: CircuitMetrics
    iterations: int
    evaluated_candidates: int
    accepted_candidates: int
    rejected_candidates: int
    termination_reason: TerminationReason


class SearchStrategy(metaclass=abc.ABCMeta):
    """Base class for user-defined circuit-search procedures."""

    @abc.abstractmethod
    def run(
        self,
        initial_circuit: Circuit,
        mutations: tp.Sequence[CircuitMutation],
        config: SearchConfig,
    ) -> SearchResult:
        """Run a bounded search and return its result."""
        raise NotImplementedError()


class ParetoHillClimber(SearchStrategy):
    """Randomised hill climber retaining a size/depth Pareto archive."""

    def run(
        self,
        initial_circuit: Circuit,
        mutations: tp.Sequence[CircuitMutation],
        config: SearchConfig,
    ) -> SearchResult:
        if config.mutation_weights is not None and len(config.mutation_weights) != len(
            mutations
        ):
            raise InvalidSearchConfigError(
                'mutation_weights must have one item per mutation.'
            )
        initial_metrics = measure_circuit(initial_circuit)
        archive: list[tuple[Circuit, CircuitMetrics]] = [
            (initial_circuit, initial_metrics)
        ]
        rng = random.Random(config.seed)
        started_at = time.monotonic()
        iterations = evaluated = accepted = rejected = 0
        while True:
            if (
                config.max_iterations is not None
                and iterations >= config.max_iterations
            ):
                termination_reason = TerminationReason.ITERATION_LIMIT
                break

            if (
                config.time_limit_sec is not None
                and time.monotonic() - started_at >= config.time_limit_sec
            ):
                termination_reason = TerminationReason.TIME_LIMIT
                break

            if not mutations:
                termination_reason = TerminationReason.NO_MUTATIONS
                break

            source, _ = rng.choice(archive)
            mutation = config.choose_random_mutation(rng=rng, mutations=mutations)

            iterations += 1
            candidate = mutation.mutate(source, rng)
            if candidate is None:
                continue
            evaluated += 1
            if (
                config.equivalence_checker is not None
                and not check_circuits_equivalence(
                    initial_circuit,
                    candidate,
                )
            ):
                rejected += 1
                continue
            candidate_metrics = measure_circuit(candidate)
            if any(metrics == candidate_metrics for _, metrics in archive) or any(
                _dominates(metrics, candidate_metrics) for _, metrics in archive
            ):
                rejected += 1
                continue
            archive = [
                (item, metrics)
                for item, metrics in archive
                if not _dominates(candidate_metrics, metrics)
            ]
            archive.append((candidate, candidate_metrics))
            accepted += 1

        archive.sort(key=lambda item: item[1])
        best, best_metrics = archive[0]
        return SearchResult(
            frontier=tuple(archive),
            best=best,
            initial_metrics=initial_metrics,
            best_metrics=best_metrics,
            iterations=iterations,
            evaluated_candidates=evaluated,
            accepted_candidates=accepted,
            rejected_candidates=rejected,
            termination_reason=termination_reason,
        )


# FIXME: need to be able to update front as whole when processing only one circuit.


def optimize(
    circuit: Circuit,
    mutations: tp.Sequence[CircuitMutation],
    config: SearchConfig,
    *,
    search_strategy: tp.Optional[SearchStrategy] = None,
) -> SearchResult:
    """Optimize ``circuit`` by running provided mutations according to the strategy."""
    _resolved_search_strategy: SearchStrategy = (
        ParetoHillClimber() if search_strategy is None else search_strategy
    )
    return _resolved_search_strategy.run(circuit, mutations, config)


def optimize_front(): ...
