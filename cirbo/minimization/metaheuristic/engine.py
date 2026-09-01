"""Extensible metaheuristic search for Boolean circuits."""

import abc
import copy
import dataclasses
import enum
import math
import random
import time
import typing as tp

from cirbo.core import Circuit
from cirbo.sat.sat import check_circuits_equivalence
from .exceptions import InvalidFrontierError, InvalidSearchConfigError
from .instance_frontier import InstanceFrontier, InstanceParetoFrontier
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

    :param max_iterations: Maximum number of iterations to run the search for.
    :param time_limit_sec: Maximum time limit in seconds to run the search for.
    :param seed: Seed for the random number generator.
    :param check_equivalence: Whether to check new found circuits for equivalence.

    """

    max_iterations: tp.Optional[int] = None
    time_limit_sec: tp.Optional[float] = None
    seed: tp.Optional[int] = None
    check_equivalence: bool = False

    def __post_init__(self) -> None:
        if self.max_iterations is None and self.time_limit_sec is None:
            raise InvalidSearchConfigError(
                'Either max_iterations or time_limit_sec must be specified.'
            )

        if self.max_iterations is not None and self.max_iterations < 0:
            raise InvalidSearchConfigError('max_iterations must be non-negative.')

        if self.time_limit_sec is not None and (
            self.time_limit_sec < 0 or not math.isfinite(self.time_limit_sec)
        ):
            raise InvalidSearchConfigError(
                'time_limit_sec must be finite and non-negative.'
            )


def choose_random_mutation(
    rng: random.Random,
    mutations: tp.Sequence[CircuitMutation],
    mutation_weights: tp.Optional[tp.Sequence[float]] = None,
) -> CircuitMutation:
    """Choose a random mutation, using weighted probabilities when specified."""
    if mutation_weights is None:
        return rng.choice(mutations)
    return rng.choices(mutations, weights=mutation_weights, k=1)[0]


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
        *,
        mutation_weights: tp.Optional[tp.Sequence[float]] = None,
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
        *,
        mutation_weights: tp.Optional[tp.Sequence[float]] = None,
    ) -> SearchResult:
        _validate_mutation_weights(mutations, mutation_weights)

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

            initial_point = rng.choice(current_frontier.get_frontier())
            mutation = choose_random_mutation(
                rng=rng,
                mutations=mutations,
                mutation_weights=mutation_weights,
            )

            _iterations += 1
            candidate = mutation.mutate(initial_point.circuit, rng)
            if candidate is None:
                continue
            _evaluated += 1

            if config.check_equivalence and not check_circuits_equivalence(
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
    instance_frontier: tp.Union[Circuit, InstanceFrontier],
    mutations: tp.Sequence[CircuitMutation],
    config: SearchConfig,
    *,
    search_strategy: tp.Optional[SearchStrategy] = None,
    mutation_weights: tp.Optional[tp.Sequence[float]] = None,
) -> SearchResult:
    """Optimize a circuit or frontier using the provided mutations and strategy."""
    _resolved_search_strategy: SearchStrategy = (
        ParetoRandomRestartHillClimber() if search_strategy is None else search_strategy
    )
    _frontier = (
        InstanceParetoFrontier([instance_frontier])
        if isinstance(instance_frontier, Circuit)
        else instance_frontier
    )

    if len(_frontier) == 0:
        raise InvalidFrontierError('The instance frontier must not be empty.')

    _validate_mutation_weights(mutations, mutation_weights)

    if config.check_equivalence:
        _frontier.validate_equivalence()

    return _resolved_search_strategy.run(
        instance_frontier=_frontier,
        mutations=mutations,
        config=config,
        mutation_weights=mutation_weights,
    )


def _validate_mutation_weights(
    mutations: tp.Sequence[CircuitMutation],
    mutation_weights: tp.Optional[tp.Sequence[float]],
) -> None:
    if mutation_weights is None:
        return

    if len(mutation_weights) != len(mutations):
        raise InvalidSearchConfigError(
            'mutation_weights must have exactly one item per mutation.'
        )

    if any(weight <= 0 or not math.isfinite(weight) for weight in mutation_weights):
        raise InvalidSearchConfigError(
            'mutation_weights must contain only finite positive values.'
        )
