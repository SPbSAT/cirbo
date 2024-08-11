import pytest

from boolean_circuit_tool.core.circuit import Circuit, Gate
from boolean_circuit_tool.core.circuit import gate
from boolean_circuit_tool.minimization.simplification import remove_leaves_and_double_not, merge_same_successors, remove_identities
from boolean_circuit_tool.minimization.simplification import _find_equivalent_gates, _replace_equivalent_gates


def test_remove_leaves_and_double_not():
    original_circuit = Circuit()
    original_circuit.add_gate(Gate('input1', gate.INPUT))
    original_circuit.add_gate(Gate('input2', gate.INPUT))
    original_circuit.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    original_circuit.emplace_gate('NOT1', gate.NOT, ('AND1',))
    original_circuit.emplace_gate('NOT2', gate.NOT, ('NOT1',))
    original_circuit.emplace_gate('leaf1', gate.NOT, ('AND1',))
    original_circuit.emplace_gate('leaf2', gate.AND, ('leaf1', 'input2',))
    original_circuit.mark_as_output('NOT2')

    simplified_circuit = remove_leaves_and_double_not(original_circuit)

    expected_circuit = Circuit()
    expected_circuit.add_gate(Gate('input1', gate.INPUT))
    expected_circuit.add_gate(Gate('input2', gate.INPUT))
    expected_circuit.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    expected_circuit.mark_as_output('AND1')

    assert simplified_circuit == expected_circuit, "Failed test 1 on remove_leaves_and_double_not"  # Check equivalence скорее

    original_circuit1 = Circuit()
    original_circuit1.add_gate(Gate('input1', gate.INPUT))
    original_circuit1.add_gate(Gate('input2', gate.INPUT))
    original_circuit1.emplace_gate('NOT1', gate.NOT, ('input1',))
    original_circuit1.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
    original_circuit1.emplace_gate('NOT2', gate.NOT, ('NOT1',))
    original_circuit1.emplace_gate('NOT3', gate.NOT, ('NOT2',))
    original_circuit1.emplace_gate('NOT4', gate.NOT, ('AND1',))
    original_circuit1.emplace_gate('NOT5', gate.NOT, ('NOT4',))
    original_circuit1.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
    original_circuit1.emplace_gate('EXTRA', gate.NOT, ('AND2',))
    original_circuit1.mark_as_output('AND2')

    simplified_circuit = remove_leaves_and_double_not(original_circuit1)

    expected_circuit1 = Circuit()
    expected_circuit1.add_gate(Gate('input1', gate.INPUT))
    expected_circuit1.add_gate(Gate('input2', gate.INPUT))
    expected_circuit1.emplace_gate('NOT1', gate.NOT, ('input1',))
    expected_circuit1.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
    expected_circuit1.emplace_gate('AND2', gate.AND, ('NOT1', 'AND1'))
    expected_circuit1.mark_as_output('AND2')

    assert simplified_circuit == expected_circuit, "Failed test 2 on remove_leaves_and_double_not"


def test_find_equivalent_gates():
    original_circuit = Circuit()
    original_circuit.add_gate(Gate('input1', gate.INPUT))
    original_circuit.add_gate(Gate('input2', gate.INPUT))
    original_circuit.emplace_gate('NOT1', gate.NOT, ('input1',))
    original_circuit.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
    original_circuit.emplace_gate('NOT2', gate.NOT, ('NOT1',))
    original_circuit.emplace_gate('NOT3', gate.NOT, ('NOT2',))
    original_circuit.emplace_gate('NOT4', gate.NOT, ('AND1',))
    original_circuit.emplace_gate('NOT5', gate.NOT, ('NOT4',))
    original_circuit.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
    original_circuit.mark_as_output('AND2')

    equivalent_groups = _find_equivalent_gates(original_circuit)
    assert sorted(equivalent_groups) == sorted([['input1', 'NOT2'], ['NOT1', 'NOT3'], ['AND1', 'NOT5', 'AND2']]), "Failed test 1 on _find_equivalent_gates"

    original_circuit1 = Circuit()
    original_circuit1.add_gate(Gate('input1', gate.INPUT))
    original_circuit1.add_gate(Gate('input2', gate.INPUT))
    original_circuit1.add_gate(Gate('input3', gate.INPUT))
    original_circuit1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    original_circuit1.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
    original_circuit1.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
    original_circuit1.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
    original_circuit1.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
    original_circuit1.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
    original_circuit1.mark_as_output('AND2')
    original_circuit1.mark_as_output('XOR2')

    equivalent_groups_1 = _find_equivalent_gates(original_circuit1)

    assert sorted(equivalent_groups_1) == [], "Failed test 1 on _find_equivalent_gates" #???


def test_replace_equivalent_gates():
    original_circuit = Circuit()
    original_circuit.add_gate(Gate('input1', gate.INPUT))
    original_circuit.add_gate(Gate('input2', gate.INPUT))
    original_circuit.add_gate(Gate('input3', gate.INPUT))
    original_circuit.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    original_circuit.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
    original_circuit.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
    original_circuit.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
    original_circuit.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
    original_circuit.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
    original_circuit.mark_as_output('AND2')
    original_circuit.mark_as_output('XOR2')

    equivalent_groups = _find_equivalent_gates(original_circuit)
    simplified_circuit = _replace_equivalent_gates(original_circuit, equivalent_groups)

    expected_circuit = Circuit()
    expected_circuit.add_gate(Gate('input1', gate.INPUT))
    expected_circuit.add_gate(Gate('input2', gate.INPUT))
    expected_circuit.add_gate(Gate('input3', gate.INPUT))
    expected_circuit.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    expected_circuit.add_gate(Gate('OR2', gate.OR, ('AND1', 'input3')))
    expected_circuit.add_gate(Gate('XOR2', gate.XOR, ('AND1', 'OR2')))
    expected_circuit.mark_as_output('AND1')
    expected_circuit.mark_as_output('XOR2')
    assert simplified_circuit == expected_circuit, "Failed test 1 on _replace_original_gates"

    original_circuit1 = Circuit()
    original_circuit1.add_gate(Gate('input1', gate.INPUT))
    original_circuit1.add_gate(Gate('input2', gate.INPUT))
    original_circuit1.emplace_gate('NOT1', gate.NOT, ('input1',))
    original_circuit1.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
    original_circuit1.emplace_gate('NOT2', gate.NOT, ('NOT1',))
    original_circuit1.emplace_gate('NOT3', gate.NOT, ('NOT2',))
    original_circuit1.emplace_gate('NOT4', gate.NOT, ('AND1',))
    original_circuit1.emplace_gate('NOT5', gate.NOT, ('NOT4',))
    original_circuit1.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
    original_circuit1.mark_as_output('AND2')

    equivalent_groups1 = _find_equivalent_gates(original_circuit1)
    simplified_circuit1 = _replace_equivalent_gates(original_circuit1, equivalent_groups1)

    expected_circuit1 = Circuit()
    expected_circuit.add_gate(Gate('input1', gate.INPUT))
    expected_circuit.add_gate(Gate('input2', gate.INPUT))
    expected_circuit.add_gate(Gate('NOT1', gate.NOT, ('input1')))
    expected_circuit.add_gate(Gate('AND1', gate.AND, ('NOT1', 'input2')))
    expected_circuit.add_gate(Gate('NOT4', gate.NOT, ('AND1')))
    expected_circuit.mark_as_output('AND1')

    assert simplified_circuit1 == expected_circuit1, "Failed test 2 on _replace_original_gates"


def test_merge_same_successors():
    original_circuit = Circuit()
    original_circuit.add_gate(Gate('input1', gate.INPUT))
    original_circuit.add_gate(Gate('input2', gate.INPUT))
    original_circuit.add_gate(Gate('input3', gate.INPUT))
    original_circuit.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
    original_circuit.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
    original_circuit.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
    original_circuit.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
    original_circuit.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
    original_circuit.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
    original_circuit.mark_as_output('AND2')
    original_circuit.mark_as_output('XOR2')

    expected_circuit = Circuit()
    expected_circuit.add_gate(Gate('input1', gate.INPUT))
    expected_circuit.add_gate(Gate('input2', gate.INPUT))
    expected_circuit.add_gate(Gate('input3', gate.INPUT))
    expected_circuit.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
    expected_circuit.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
    expected_circuit.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
    expected_circuit.mark_as_output('AND2')
    expected_circuit.mark_as_output('XOR2')

    simplified_circuit = merge_same_successors(original_circuit)

    assert simplified_circuit == expected_circuit, "Failed test on merge_same_successors"


def test_remove_identities():
    original_circuit = Circuit()
    original_circuit.add_gate(Gate('input1', gate.INPUT))
    original_circuit.add_gate(Gate('input2', gate.INPUT))
    original_circuit.emplace_gate('XOR1', gate.XOR, ('input1', 'input1'))  # AND(X, X) -> X
    original_circuit.emplace_gate('NOT', gate.NOT, ('input2',))
    original_circuit.emplace_gate('AND1', gate.AND, ('input2', 'NOT1',))
    original_circuit.emplace_gate('OR1', gate.OR, ('XOR1', 'AND1'))
    original_circuit.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
    original_circuit.mark_as_output('OR1')

    expected_circuit = Circuit()
    expected_circuit.add_gate(Gate('input1', gate.INPUT))
    expected_circuit.add_gate(Gate('input2', gate.INPUT))
    expected_circuit.add_gate(Gate('XOR1', gate.ALWAYS_FALSE, ()))
    expected_circuit.add_gate(Gate('NOT1', gate.NOT, ('input2',)))
    expected_circuit.add_gate(Gate('AND1', gate.ALWAYS_FALSE, ()))
    expected_circuit.add_gate(Gate('OR1', gate.ALWAYS_FALSE, ()))
    expected_circuit.add_gate(Gate('AND2', gate.AND, ('input1', 'input2')))
    expected_circuit.mark_as_output('OR1')

    simplified_circuit = remove_identities(original_circuit)

    assert simplified_circuit == expected_circuit, "Failed test on remove_identities"
