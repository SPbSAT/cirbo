import pytest

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.minimization.simplification import (
    _find_equivalent_gates,
    _replace_equivalent_gates,
    merge_same_successors,
    remove_identities,
    remove_leaves_and_double_not,
)


def are_circuits_isomorphic(circuit1: Circuit, circuit2: Circuit) -> bool:
    def topological_sort_compare(circuit: Circuit, inverse: bool = False) -> list[Gate]:
        return list(circuit.top_sort(inverse=inverse))

    sorted_gates1 = topological_sort_compare(circuit1)
    sorted_gates2 = topological_sort_compare(circuit2)

    if len(sorted_gates1) != len(sorted_gates2):
        return False

    for gate1, gate2 in zip(sorted_gates1, sorted_gates2):
        if gate1.gate_type != gate2.gate_type:
            return False

        if len(gate1.operands) != len(gate2.operands):
            return False

    return True


# Test case 1 for remove_leaves_and_double_not
original_circuit_1 = Circuit()
original_circuit_1.add_gate(Gate('input1', gate.INPUT))
original_circuit_1.add_gate(Gate('input2', gate.INPUT))
original_circuit_1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_1.emplace_gate('NOT1', gate.NOT, ('AND1',))
original_circuit_1.emplace_gate('NOT2', gate.NOT, ('NOT1',))
original_circuit_1.emplace_gate('leaf1', gate.NOT, ('AND1',))
original_circuit_1.emplace_gate(
    'leaf2',
    gate.AND,
    (
        'leaf1',
        'input2',
    ),
)
original_circuit_1.mark_as_output('NOT2')

expected_circuit_1 = Circuit()
expected_circuit_1.add_gate(Gate('input1', gate.INPUT))
expected_circuit_1.add_gate(Gate('input2', gate.INPUT))
expected_circuit_1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
expected_circuit_1.mark_as_output('AND1')

# Test case 2 for remove_leaves_and_double_not
original_circuit_2 = Circuit()
original_circuit_2.add_gate(Gate('input1', gate.INPUT))
original_circuit_2.add_gate(Gate('input2', gate.INPUT))
original_circuit_2.emplace_gate('NOT1', gate.NOT, ('input1',))
original_circuit_2.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
original_circuit_2.emplace_gate('NOT2', gate.NOT, ('NOT1',))
original_circuit_2.emplace_gate('NOT3', gate.NOT, ('NOT2',))
original_circuit_2.emplace_gate('NOT4', gate.NOT, ('AND1',))
original_circuit_2.emplace_gate('NOT5', gate.NOT, ('NOT4',))
original_circuit_2.emplace_gate('AND2', gate.AND, ('NOT3', 'NOT5'))
original_circuit_2.emplace_gate('EXTRA', gate.NOT, ('AND2',))
original_circuit_2.mark_as_output('AND2')

expected_circuit_2 = Circuit()
expected_circuit_2.add_gate(Gate('input1', gate.INPUT))
expected_circuit_2.add_gate(Gate('input2', gate.INPUT))
expected_circuit_2.emplace_gate('NOT1', gate.NOT, ('input1',))
expected_circuit_2.emplace_gate('AND1', gate.AND, ('NOT1', 'input2'))
expected_circuit_2.emplace_gate('AND2', gate.AND, ('NOT1', 'AND1'))
expected_circuit_2.mark_as_output('AND2')


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        (original_circuit_1, expected_circuit_1),
        (original_circuit_2, expected_circuit_2),
    ],
)
def test_remove_leaves_and_double_not(
    original_circuit: Circuit, expected_circuit: Circuit
):
    simplified_circuit = remove_leaves_and_double_not(original_circuit)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on remove_leaves_and_double_not"


# Test case 1 for _find_equivalent_gates
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

# Test case 2 for _find_equivalent_gates
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
@pytest.mark.skip(reason="need to be fixed")
def test_find_equivalent_gates(original_circuit: Circuit, expected_groups):
    equivalent_groups = _find_equivalent_gates(original_circuit)
    assert sorted(equivalent_groups) == sorted(
        expected_groups
    ), "Failed test on _find_equivalent_gates"


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
@pytest.mark.skip(reason="need to be fixed")
def test_replace_equivalent_gates(original_circuit: Circuit, expected_circuit: Circuit):
    equivalent_groups = _find_equivalent_gates(original_circuit)
    simplified_circuit = _replace_equivalent_gates(original_circuit, equivalent_groups)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on _replace_equivalent_gates"


# Test case 1 for merge_same_successors
original_circuit_6 = Circuit()
original_circuit_6.add_gate(Gate('input1', gate.INPUT))
original_circuit_6.add_gate(Gate('input2', gate.INPUT))
original_circuit_6.add_gate(Gate('input3', gate.INPUT))
original_circuit_6.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_6.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_6.emplace_gate('OR1', gate.OR, ('AND2', 'input3'))
original_circuit_6.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
original_circuit_6.emplace_gate('XOR1', gate.XOR, ('AND2', 'OR1'))
original_circuit_6.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
original_circuit_6.mark_as_output('AND2')
original_circuit_6.mark_as_output('XOR2')

expected_circuit_6 = Circuit()
expected_circuit_6.add_gate(Gate('input1', gate.INPUT))
expected_circuit_6.add_gate(Gate('input2', gate.INPUT))
expected_circuit_6.add_gate(Gate('input3', gate.INPUT))
expected_circuit_6.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
expected_circuit_6.emplace_gate('OR2', gate.OR, ('AND2', 'input3'))
expected_circuit_6.emplace_gate('XOR2', gate.XOR, ('AND2', 'OR2'))
expected_circuit_6.mark_as_output('AND2')
expected_circuit_6.mark_as_output('XOR2')


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        (original_circuit_6, expected_circuit_6),
    ],
)
@pytest.mark.skip(reason="need to be fixed")
def test_merge_same_successors(original_circuit: Circuit, expected_circuit: Circuit):
    simplified_circuit = merge_same_successors(original_circuit)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on merge_same_successors"


# Test case 1 for remove_identities
original_circuit_7 = Circuit()
original_circuit_7.add_gate(Gate('input1', gate.INPUT))
original_circuit_7.add_gate(Gate('input2', gate.INPUT))
original_circuit_7.emplace_gate('XOR1', gate.XOR, ('input1', 'input1'))
original_circuit_7.emplace_gate('NOT', gate.NOT, ('input2',))
original_circuit_7.emplace_gate(
    'AND1',
    gate.AND,
    (
        'input2',
        'NOT',
    ),
)
original_circuit_7.emplace_gate('OR1', gate.OR, ('XOR1', 'AND1'))
original_circuit_7.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_7.mark_as_output('OR1')

expected_circuit_7 = Circuit()
expected_circuit_7.add_gate(Gate('input1', gate.INPUT))
expected_circuit_7.add_gate(Gate('input2', gate.INPUT))
expected_circuit_7.add_gate(Gate('XOR1', gate.ALWAYS_FALSE, ()))
expected_circuit_7.add_gate(Gate('NOT', gate.NOT, ('input2',)))
expected_circuit_7.add_gate(Gate('AND1', gate.ALWAYS_FALSE, ()))
expected_circuit_7.add_gate(Gate('OR1', gate.ALWAYS_FALSE, ()))
expected_circuit_7.add_gate(Gate('AND2', gate.AND, ('input1', 'input2')))
expected_circuit_7.mark_as_output('OR1')


@pytest.mark.parametrize(
    "original_circuit, expected_circuit",
    [
        (original_circuit_7, expected_circuit_7),
    ],
)
@pytest.mark.skip(reason="need to be fixed")
def test_remove_identities(original_circuit: Circuit, expected_circuit: Circuit):
    simplified_circuit = remove_identities(original_circuit)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on remove_identities"
