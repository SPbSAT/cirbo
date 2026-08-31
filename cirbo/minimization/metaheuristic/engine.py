"""Extensible metaheuristic search for Boolean circuits."""

import abc
import copy
import dataclasses
import enum
import random
import time
import typing as tp

from cirbo.sat.sat import check_circuits_equivalence
from .exceptions import InvalidSearchConfigError
from .instance_frontier import (
    measure_circuit,
    InstanceFrontier,
)
from .mutation import CircuitMutation

__all__ = [
    'SearchConfig',
    'SearchResult',
    'TerminationReason',
    'SearchStrategy',
    'ParetoRandomRestartHillClimber',
    'optimize',
]


@dataclasses.dataclass(frozen=True)
class SearchConfig:
    """
    Bounded-run and candidate-validation settings for a search.

    :max_iterations: Maximum number of iterations to run the search for.
    :time_limit_sec: Maximum time limit in seconds to run the search for.
    :seed: Seed for the random number generator.
    :mutation_weights: Weights (probabilities) for the mutations.
    :check_equivalence: Whether to check new found circuits for equivalence.
    """

    max_iterations: tp.Optional[int] = None
    time_limit_sec: tp.Optional[float] = None
    seed: tp.Optional[int] = None
    mutation_weights: tp.Optional[tp.Sequence[float]] = None
    check_equivalence: bool = False

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

    UNKNOWN = 'unknown'
    ITERATION_LIMIT = 'iteration_limit'
    TIME_LIMIT = 'time_limit'
    NO_MUTATIONS = 'no_mutations'


@dataclasses.dataclass(frozen=True)
class SearchResult:
    """Result and accounting data produced by a search strategy."""

    frontier: InstanceFrontier
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
        instance_frontier: InstanceFrontier,
        mutations: tp.Sequence[CircuitMutation],
        config: SearchConfig,
    ) -> SearchResult:
        """Run a bounded search and return its result."""
        raise NotImplementedError()


class ParetoRandomRestartHillClimber(SearchStrategy):
    """Randomized hill climber retaining a size/depth Pareto archive."""

    def run(
        self,
        instance_frontier: InstanceFrontier,
        mutations: tp.Sequence[CircuitMutation],
        config: SearchConfig,
    ) -> SearchResult:
        if config.mutation_weights is not None and len(config.mutation_weights) != len(
            mutations
        ):
            raise InvalidSearchConfigError(
                "Config's `mutation_weights` must have exactly one item per mutation."
            )

        current_frontier = copy.deepcopy(instance_frontier)

        rng = random.Random(config.seed)

        _started_at = time.monotonic()
        _iterations = 0
        _evaluated = 0
        _accepted = 0
        _rejected = 0

        _termination_reason: TerminationReason = TerminationReason.UNKNOWN

        if not mutations:
            _termination_reason = TerminationReason.NO_MUTATIONS

        while _termination_reason == TerminationReason.UNKNOWN:
            if (
                config.max_iterations is not None
                and _iterations >= config.max_iterations
            ):
                _termination_reason = TerminationReason.ITERATION_LIMIT
                break

            if (
                config.time_limit_sec is not None
                and time.monotonic() - _started_at >= config.time_limit_sec
            ):
                _termination_reason = TerminationReason.TIME_LIMIT
                break

            initial_point = rng.choice(current_frontier.get_front())
            mutation = config.choose_random_mutation(rng=rng, mutations=mutations)

            _iterations += 1
            candidate = mutation.mutate(initial_point.circuit, rng)
            if candidate is None:
                continue
            _evaluated += 1

            if config.check_equivalence is not None and not check_circuits_equivalence(
                current_frontier.any_instance(rng=rng).circuit,
                candidate,
            ):
                _rejected += 1
                continue

            if current_frontier.consider_circuit(candidate):
                _accepted += 1
            else:
                _rejected += 1

        return SearchResult(
            frontier=current_frontier,
            iterations=_iterations,
            evaluated_candidates=_evaluated,
            accepted_candidates=_accepted,
            rejected_candidates=_rejected,
            termination_reason=_termination_reason,
        )


def optimize(
    instance_frontier: InstanceFrontier,
    mutations: tp.Sequence[CircuitMutation],
    config: SearchConfig,
    *,
    search_strategy: tp.Optional[SearchStrategy] = None,
) -> SearchResult:
    """Optimize ``instance_frontier`` by running provided mutations according to the strategy."""
    _resolved_search_strategy: SearchStrategy = (
        ParetoRandomRestartHillClimber() if search_strategy is None else search_strategy
    )
    return _resolved_search_strategy.run(
        instance_frontier=instance_frontier,
        mutations=mutations,
        config=config,
    )
