import pytest

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.minimization.simplification import CollapseEquivalentGates
from boolean_circuit_tool.minimization.simplification.collapse_equivalent_gates import (
    _find_equivalent_gates_groups,
)

from ._utils import are_circuits_isomorphic


# Test case 1 for _find_equivalent_gates_groups
original_circuit_3 = Circuit()
original_circuit_3.add_gate(Gate('input1', gate.INPUT))
original_circuit_3.add_gate(Gate('input2', gate.INPUT))
original_circuit_3.emplace_gate('NOT1', gate.NOT, ('input1',))
original_circuit_3.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
original_circuit_3.emplace_gate('NOT2', gate.NOT, ('NOT1',))
original_circuit_3.emplace_gate('NOT3', gate.NOT, ('NOT2',))
original_circuit_3.emplace_gate('NOT4', gate.NOT, ('AND1',))
original_circuit_3.emplace_gate('NOT5', gate.NOT, ('NOT4',))
original_circuit_3.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
original_circuit_3.mark_as_output('AND2')

expected_groups_3 = [['input1', 'NOT2'], ['NOT1', 'NOT3'], ['AND1', 'NOT5', 'AND2']]

# Test case 2 for _find_equivalent_gates_groups
original_circuit_4 = Circuit()
original_circuit_4.add_gate(Gate('input1', gate.INPUT))
original_circuit_4.add_gate(Gate('input2', gate.INPUT))
original_circuit_4.add_gate(Gate('input3', gate.INPUT))
original_circuit_4.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_4.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_4.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
original_circuit_4.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
original_circuit_4.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
original_circuit_4.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
original_circuit_4.mark_as_output('AND2')
original_circuit_4.mark_as_output('XOR2')

expected_groups_4 = [['AND1', 'AND2'], ['OR1', 'OR2'], ['XOR1', 'XOR2']]


@pytest.mark.parametrize(
    "original_circuit, expected_groups",
    [
        (original_circuit_3, expected_groups_3),
        (original_circuit_4, expected_groups_4),
    ],
)
def test_find_equivalent_gates(original_circuit: Circuit, expected_groups):
    equivalent_groups = _find_equivalent_gates_groups(original_circuit)
    assert sorted(map(sorted, equivalent_groups)) == sorted(
        map(sorted, expected_groups)
    )


# Test case 1 for _replace_equivalent_gates
original_circuit_5 = Circuit()
original_circuit_5.add_gate(Gate('input1', gate.INPUT))
original_circuit_5.add_gate(Gate('input2', gate.INPUT))
original_circuit_5.add_gate(Gate('input3', gate.INPUT))
original_circuit_5.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_5.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_5.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
original_circuit_5.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
original_circuit_5.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
original_circuit_5.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
original_circuit_5.mark_as_output('AND2')
original_circuit_5.mark_as_output('XOR2')

expected_circuit_5 = Circuit()
expected_circuit_5.add_gate(Gate('input1', gate.INPUT))
expected_circuit_5.add_gate(Gate('input2', gate.INPUT))
expected_circuit_5.add_gate(Gate('input3', gate.INPUT))
expected_circuit_5.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
expected_circuit_5.add_gate(Gate('OR2', gate.OR, ('AND1', 'input3')))
expected_circuit_5.add_gate(Gate('XOR2', gate.XOR, ('AND1', 'OR2')))
expected_circuit_5.mark_as_output('AND1')
expected_circuit_5.mark_as_output('XOR2')


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        (original_circuit_5, expected_circuit_5),
    ],
)
def test_collapse_equivalent_gates(
    original_circuit: Circuit, expected_circuit: Circuit
):
    simplified_circuit = CollapseEquivalentGates().transform(original_circuit)
    assert are_circuits_isomorphic(simplified_circuit, expected_circuit)
