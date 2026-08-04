import random

import pytest

from cirbo.core import Circuit, Gate, gate
from cirbo.minimization.metaheuristic import (
    abc as abc_mutations,
    ABC_EASY_COMMANDS,
    ABC_HARD_COMMANDS,
    ABCEasyMutation,
    ABCHardMutation,
    ABCUnavailableError,
)


def _circuit() -> Circuit:
    circuit = Circuit.bare_circuit(2)
    circuit.add_gate(Gate('output', gate.AND, ('0', '1')))
    circuit.mark_as_output('output')
    return circuit


@pytest.mark.parametrize(
    'mutation_type, commands',
    [(ABCEasyMutation, ABC_EASY_COMMANDS), (ABCHardMutation, ABC_HARD_COMMANDS)],
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
    assert calls == [mutation.last_command]
    assert mutation.last_command in commands


def test_hard_commands_extend_easy_commands():
    assert ABC_HARD_COMMANDS[: len(ABC_EASY_COMMANDS)] == ABC_EASY_COMMANDS
    assert 'rewire -I 20; b; ps' in ABC_HARD_COMMANDS
    assert '&get; &deepsyn -I 1 -J 20; &put; ps' in ABC_HARD_COMMANDS


def test_abc_mutation_reports_missing_extension(monkeypatch):
    def unavailable():
        raise ABCUnavailableError('extension is unavailable')

    monkeypatch.setattr(abc_mutations, '_get_abc_transform', unavailable)

    with pytest.raises(ABCUnavailableError, match='extension is unavailable'):
        ABCEasyMutation().mutate(_circuit(), random.Random(1))
