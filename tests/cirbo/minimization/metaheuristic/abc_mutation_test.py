import random

import pytest

from cirbo.core import Circuit, Gate, gate
from cirbo.integrations import abc
from cirbo.minimization.metaheuristic import (
    abc as metaheuristics_abc,
    ABC_HEAVY_COMMANDS,
    ABCHeavyMutation,
)


def _circuit() -> Circuit:
    circuit = Circuit.bare_circuit(2)
    circuit.add_gate(Gate('output', gate.AND, ('0', '1')))
    circuit.mark_as_output('output')
    return circuit


@pytest.mark.parametrize(
    'mutation_type, commands',
    [
        (ABCHeavyMutation, ABC_HEAVY_COMMANDS),
    ],
)
def test_abc_mutation_selects_a_command(monkeypatch, mutation_type, commands):
    calls = []

    def transform(circuit, command):
        calls.append(command)
        return circuit

    monkeypatch.setattr(metaheuristics_abc, 'abc_transform', transform)
    mutation = mutation_type()
    result = mutation.mutate(_circuit(), random.Random(17))

    assert result.get_truth_table() == _circuit().get_truth_table()
    assert mutation.last_command is not None
    assert calls == [mutation.last_command]
    assert mutation.last_command.removeprefix('strash;') in set(
        cmd.script for cmd in commands
    )


def test_abc_transform_propagates_unavailable_error(monkeypatch):
    def unavailable(*args, **kwargs):
        raise abc.ABCUnavailableError(
            'ABC support is not available in this Cirbo installation'
        )

    monkeypatch.setattr(abc, '_run_abc_commands', unavailable)

    with pytest.raises(
        abc.ABCUnavailableError,
        match='ABC support is not available',
    ):
        abc.abc_transform(_circuit(), 'strash;')


def test_abc_mutation_propagates_transform_error(monkeypatch):
    def unavailable(*args, **kwargs):
        raise abc.ABCUnavailableError('extension is unavailable')

    monkeypatch.setattr(metaheuristics_abc, 'abc_transform', unavailable)

    with pytest.raises(abc.ABCUnavailableError, match='extension is unavailable'):
        ABCHeavyMutation().mutate(_circuit(), random.Random(1))


@pytest.mark.parametrize(
    'command',
    ABC_HEAVY_COMMANDS,
)
@pytest.mark.ABC
def test_all_abc_commands_are_valid(monkeypatch, command):
    commands = [command]
    monkeypatch.setattr(ABCHeavyMutation, '_commands', commands)

    ckt = ABCHeavyMutation().mutate(_circuit(), random.Random(1))
    assert isinstance(ckt, Circuit)
