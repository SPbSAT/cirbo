import pytest

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.minimization.simplification import MergeEquivalentGates
from boolean_circuit_tool.minimization.simplification.merge_equivalent_gates import (
    _find_equivalent_gates_groups,
)


# Test case 1 for _find_equivalent_gates_groups
original_circuit_1 = Circuit()
original_circuit_1.add_gate(Gate('input1', gate.INPUT))
original_circuit_1.add_gate(Gate('input2', gate.INPUT))
original_circuit_1.emplace_gate('NOT1', gate.NOT, ('input1',))
original_circuit_1.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
original_circuit_1.emplace_gate('NOT2', gate.NOT, ('NOT1',))
original_circuit_1.emplace_gate('NOT3', gate.NOT, ('NOT2',))
original_circuit_1.emplace_gate('NOT4', gate.NOT, ('AND1',))
original_circuit_1.emplace_gate('NOT5', gate.NOT, ('NOT4',))
original_circuit_1.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
original_circuit_1.mark_as_output('AND2')

expected_groups_1 = [['input1', 'NOT2'], ['NOT1', 'NOT3'], ['AND1', 'NOT5', 'AND2']]

# Test case 2 for _find_equivalent_gates_groups
original_circuit_2 = Circuit()
original_circuit_2.add_gate(Gate('input1', gate.INPUT))
original_circuit_2.add_gate(Gate('input2', gate.INPUT))
original_circuit_2.add_gate(Gate('input3', gate.INPUT))
original_circuit_2.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_2.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_2.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
original_circuit_2.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
original_circuit_2.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
original_circuit_2.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
original_circuit_2.mark_as_output('AND2')
original_circuit_2.mark_as_output('XOR2')

expected_groups_2 = [['AND1', 'AND2'], ['OR1', 'OR2'], ['XOR1', 'XOR2']]


@pytest.mark.parametrize(
    "original_circuit, expected_groups",
    [
        (original_circuit_1, expected_groups_1),
        (original_circuit_2, expected_groups_2),
    ],
)
def test_find_equivalent_gates(original_circuit: Circuit, expected_groups):
    equivalent_groups = _find_equivalent_gates_groups(original_circuit)
    assert sorted(map(sorted, equivalent_groups)) == sorted(
        map(sorted, expected_groups)
    )


# Test case 1 for _replace_equivalent_gates
original_circuit_3 = Circuit()
original_circuit_3.add_gate(Gate('input1', gate.INPUT))
original_circuit_3.add_gate(Gate('input2', gate.INPUT))
original_circuit_3.add_gate(Gate('input3', gate.INPUT))
original_circuit_3.add_gate(Gate('input4', gate.INPUT))
original_circuit_3.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_3.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_3.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
original_circuit_3.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
original_circuit_3.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
original_circuit_3.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
original_circuit_3.mark_as_output('AND2')
original_circuit_3.mark_as_output('XOR1')
original_circuit_3.mark_as_output('XOR2')

expected_circuit_3 = Circuit()
expected_circuit_3.add_gate(Gate('input1', gate.INPUT))
expected_circuit_3.add_gate(Gate('input2', gate.INPUT))
expected_circuit_3.add_gate(Gate('input3', gate.INPUT))
expected_circuit_3.add_gate(Gate('input4', gate.INPUT))
expected_circuit_3.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
expected_circuit_3.add_gate(Gate('OR2', gate.OR, ('AND2', 'input3')))
expected_circuit_3.add_gate(Gate('XOR2', gate.XOR, ('AND2', 'OR2')))
expected_circuit_3.mark_as_output('AND2')
expected_circuit_3.mark_as_output('XOR2')
expected_circuit_3.mark_as_output('XOR2')


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        (original_circuit_3, expected_circuit_3),
    ],
)
def test_merge_equivalent_gates(
    original_circuit: Circuit,
    expected_circuit: Circuit,
):
    simplified_circuit = MergeEquivalentGates().transform(original_circuit)
    assert simplified_circuit.inputs == expected_circuit.inputs
    assert simplified_circuit.outputs == expected_circuit.outputs
    assert (
        simplified_circuit.get_gates_truth_table()
        == expected_circuit.get_gates_truth_table()
    )
