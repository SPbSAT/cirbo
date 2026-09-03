import random

import pytest

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization.metaheuristic import (
    abc as abc_mutations,
    ABC_HEAVY_COMMANDS,
    ABC_LIGHT_COMMANDS,
    ABCHeavyMutation,
    ABCLightMutation,
    ABCUnavailableError,
)


def _circuit() -> Circuit:
    circuit = Circuit.bare_circuit(2)
    circuit.add_gate(Gate('output', gate.AND, ('0', '1')))
    circuit.mark_as_output('output')
    return circuit


@pytest.mark.parametrize(
    'mutation_type, commands',
    [
        (ABCLightMutation, ABC_LIGHT_COMMANDS),
        (ABCHeavyMutation, ABC_HEAVY_COMMANDS),
    ],
)
def test_abc_mutation_selects_a_command(monkeypatch, mutation_type, commands):
    calls = []

    def transform(circuit, command):
        calls.append(command)
        return circuit

    monkeypatch.setattr(abc_mutations, '_get_abc_transform', lambda: transform)
    mutation = mutation_type()
    result = mutation.mutate(_circuit(), random.Random(17))

    assert result.get_truth_table() == _circuit().get_truth_table()
    assert mutation.last_command is not None
    assert calls == [mutation.last_command]
    assert mutation.last_command.removeprefix('strash;') in commands


def test_hard_commands_extend_easy_commands():
    assert ABC_HEAVY_COMMANDS[: len(ABC_LIGHT_COMMANDS)] == ABC_LIGHT_COMMANDS


def test_abc_mutation_reports_missing_extension(monkeypatch):
    def unavailable():
        raise ABCUnavailableError('extension is unavailable')

    monkeypatch.setattr(abc_mutations, '_get_abc_transform', unavailable)

    with pytest.raises(ABCUnavailableError, match='extension is unavailable'):
        ABCLightMutation().mutate(_circuit(), random.Random(1))


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
