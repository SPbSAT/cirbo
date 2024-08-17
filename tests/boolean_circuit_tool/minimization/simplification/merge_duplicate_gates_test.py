import pytest

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.minimization.simplification import MergeDuplicateGates


original_1 = Circuit()
original_1.add_inputs(['I1', 'I2', 'I3'])
original_1.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
original_1.emplace_gate('AND2', gate.AND, ('I2', 'I1'))
original_1.set_outputs(['AND2'])


expected_1 = Circuit()
expected_1.add_inputs(['I1', 'I2', 'I3'])
expected_1.emplace_gate('AND2', gate.AND, ('I1', 'I2'))
expected_1.set_outputs(['AND2'])


original_2 = Circuit()
original_2.add_inputs(['I1', 'I2', 'I3'])
original_2.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
original_2.emplace_gate('AND2', gate.AND, ('I2', 'I1'))
original_2.emplace_gate('NOT', gate.NOT, ('AND1',))
original_2.emplace_gate('IFF', gate.NOT, ('AND2',))
original_2.set_outputs(['IFF', 'NOT'])


expected_2 = Circuit()
expected_2.add_inputs(['I1', 'I2', 'I3'])
expected_2.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
expected_2.emplace_gate('NOT', gate.NOT, ('AND1',))
expected_2.emplace_gate('IFF', gate.NOT, ('AND1',))
expected_2.set_outputs(['IFF', 'NOT'])


@pytest.mark.parametrize(
    'original, expected',
    [
        (original_1, expected_1),
        (original_2, expected_2),
    ],
)
def test_merge_duplicate_gates(original, expected):
    simplified = MergeDuplicateGates().transform(original)
    assert simplified.inputs == expected.inputs
    assert simplified.outputs == expected.outputs
    assert simplified.get_gates_truth_table() == expected.get_gates_truth_table()
