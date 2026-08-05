import random

import pytest

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization.metaheuristic import (
    CircuitMetrics,
    CircuitMutation,
    InvalidSearchConfigError,
    measure_circuit,
    optimize,
    SearchConfig,
)
from cirbo.minimization.metaheuristic.engine import TerminationReason


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


def test_measure_circuit():
    assert measure_circuit(_duplicate_and_circuit()) == CircuitMetrics(5, 2)


def test_pareto_search_uses_test_mutation():
    source = _duplicate_and_circuit()
    candidate = _simplified_and_circuit()
    result = optimize(
        source,
        [_FixedMutation(candidate)],
        SearchConfig(max_iterations=2, seed=1),
    )
    assert candidate.get_truth_table() == source.get_truth_table()
    assert result.best_metrics == CircuitMetrics(3, 1)
    assert result.accepted_candidates == 1
    assert result.termination_reason == TerminationReason.ITERATION_LIMIT


def test_pareto_search_rejects_equal_metrics():
    result = optimize(
        _duplicate_and_circuit(),
        [_IdentityMutation()],
        SearchConfig(max_iterations=1),
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
