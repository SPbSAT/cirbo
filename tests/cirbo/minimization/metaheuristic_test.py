import random

import pytest

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization.metaheuristic import (
    CircuitMetrics,
    CircuitMutation,
    InstanceDescriptor,
    InvalidFrontierError,
    InvalidSearchConfigError,
    MultiStartRandomWalk,
    optimize,
    ParetoFrontier,
    SearchConfig,
    SearchResult,
    SearchStrategy,
)
from cirbo.minimization.metaheuristic.search import TerminationReason


def _duplicate_and_circuit() -> Circuit:
    circuit = Circuit.bare_circuit(2)
    circuit.add_gate(Gate('and_1', gate.AND, ('0', '1')))
    circuit.add_gate(Gate('and_2', gate.AND, ('0', '1')))
    circuit.add_gate(Gate('out', gate.OR, ('and_1', 'and_2')))
    circuit.mark_as_output('out')
    return circuit


def _simplified_and_circuit() -> Circuit:
    circuit = Circuit.bare_circuit(2)
    circuit.add_gate(Gate('out', gate.AND, ('0', '1')))
    circuit.mark_as_output('out')
    return circuit


class _FixedMutation(CircuitMutation):
    """Test mutation returning a predetermined equivalent circuit."""

    def __init__(self, result: Circuit):
        self._result = result

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        del circuit, rng
        return self._result


class _IdentityMutation(CircuitMutation):
    """Test mutation that returns its input unchanged."""

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        del rng
        return circuit


class _CountingMutation(_IdentityMutation):
    def __init__(self):
        self.calls = 0

    def mutate(self, circuit: Circuit, rng: random.Random) -> Circuit:
        self.calls += 1
        return super().mutate(circuit, rng)


class _RecordingStrategy(SearchStrategy):
    def __init__(self):
        self.mutation_weights = None

    def run(
        self,
        instance_frontier,
        mutations,
        config,
        *,
        mutation_weights=None,
    ) -> SearchResult:
        self.mutation_weights = mutation_weights
        return MultiStartRandomWalk().run(
            instance_frontier,
            mutations,
            config,
            mutation_weights=mutation_weights,
        )


def test_measure_circuit():
    assert CircuitMetrics.from_circuit(_duplicate_and_circuit()) == CircuitMetrics(3, 2)


def test_pareto_search_uses_test_mutation():
    source = _duplicate_and_circuit()
    candidate = _simplified_and_circuit()
    result = optimize(
        source,
        [_FixedMutation(candidate)],
        SearchConfig(max_iterations=2, seed=1),
    )
    assert candidate.get_truth_table() == source.get_truth_table()
    assert result.frontier.get_frontier()[0].metrics == CircuitMetrics(1, 1)
    assert result.accepted_candidates == 1
    assert result.termination_reason == TerminationReason.ITERATION_LIMIT


def test_pareto_search_rejects_equal_metrics():
    result = optimize(
        _duplicate_and_circuit(),
        [_IdentityMutation()],
        SearchConfig(max_iterations=1, check_equivalence=True),
        search_strategy=MultiStartRandomWalk(1),
    )
    assert result.accepted_candidates == 0
    assert result.rejected_candidates == 1


def test_search_configuration_requires_bound():
    with pytest.raises(InvalidSearchConfigError):
        SearchConfig()


def test_search_without_mutations_stops_immediately():
    result = optimize(_duplicate_and_circuit(), [], SearchConfig(max_iterations=2))
    assert result.termination_reason == TerminationReason.NO_MUTATIONS
    assert result.iterations == 0


def test_search_uses_separate_mutation_weights():
    first = _CountingMutation()
    second = _CountingMutation()
    result = optimize(
        _duplicate_and_circuit(),
        [first, second],
        SearchConfig(max_iterations=3, seed=1),
        mutation_weights=[1e-100, 1.0],
        search_strategy=MultiStartRandomWalk(1),
    )
    assert first.calls == 0
    assert second.calls == 3
    assert result.rejected_candidates == 3


def test_search_passes_weights_to_custom_strategy():
    strategy = _RecordingStrategy()
    weights = [2.0]
    optimize(
        _duplicate_and_circuit(),
        [_IdentityMutation()],
        SearchConfig(max_iterations=0),
        mutation_weights=weights,
        search_strategy=strategy,
    )
    assert strategy.mutation_weights is weights


@pytest.mark.parametrize(
    'weights', [[1.0, 2.0], [0.0], [-1.0], [float('nan')], [float('inf')]]
)
def test_search_rejects_invalid_mutation_weights(weights):
    with pytest.raises(InvalidSearchConfigError):
        optimize(
            _duplicate_and_circuit(),
            [_IdentityMutation()],
            SearchConfig(max_iterations=1),
            mutation_weights=weights,
        )


@pytest.mark.parametrize('time_limit_sec', [-1.0, float('nan'), float('inf')])
def test_search_rejects_invalid_time_limit(time_limit_sec):
    with pytest.raises(InvalidSearchConfigError):
        SearchConfig(time_limit_sec=time_limit_sec)


def test_search_rejects_empty_frontier():
    with pytest.raises(InvalidFrontierError, match='must not be empty'):
        optimize(
            ParetoFrontier([]),
            [_IdentityMutation()],
            SearchConfig(max_iterations=1),
        )


def test_frontier_validates_equivalence():
    frontier = ParetoFrontier([_duplicate_and_circuit()])
    frontier.instances.append(
        InstanceDescriptor.from_circuit(_simplified_and_circuit())
    )
    frontier.validate_equivalence()

    different = Circuit.bare_circuit(2)
    different.add_gate(Gate('out', gate.OR, ('0', '1')))
    different.mark_as_output('out')
    frontier.instances.append(InstanceDescriptor.from_circuit(different))
    with pytest.raises(InvalidFrontierError, match='must be equivalent'):
        frontier.validate_equivalence()


def test_optimize_validates_frontier_only_when_enabled(monkeypatch):
    frontier = ParetoFrontier([_duplicate_and_circuit()])
    calls = []
    monkeypatch.setattr(frontier, 'validate_equivalence', lambda: calls.append(True))

    optimize(frontier, [], SearchConfig(max_iterations=0))
    assert calls == []

    optimize(frontier, [], SearchConfig(max_iterations=0, check_equivalence=True))
    assert calls == [True]
