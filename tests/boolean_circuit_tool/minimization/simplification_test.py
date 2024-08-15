import pytest

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.minimization.simplification import (
    collapse_unary_operators,
    remove_redundant_gates,
)
from boolean_circuit_tool.minimization.simplification._simplification_bu import (
    collapse_equivalent_gates_sparse,
    remove_identities,
)
from boolean_circuit_tool.minimization.simplification.collapse_equivalent_gates import (
    _find_equivalent_gates_groups,
    _replace_equivalent_gates,
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


def test_remove_redundant_gates():
    original = Circuit()
    original.add_inputs(['I1', 'I2', 'I3', 'I4'])
    original.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
    original.emplace_gate('EX1', gate.NOT, ('AND1',))
    original.emplace_gate('NOT1', gate.NOT, ('I1', 'I2'))
    original.emplace_gate('EX2', gate.AND, ('NOT1', 'I3'))
    original.emplace_gate('OUT1', gate.AND, ('NOT1', 'AND1'))
    original.emplace_gate('OUT2', gate.NOT, ('I4',))
    original.emplace_gate('EX3', gate.NOT, ('OUT2',))
    original.set_outputs(['OUT1', 'OUT2'])

    expected = Circuit()
    expected.add_inputs(['I1', 'I2', 'I3', 'I4'])
    expected.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
    expected.emplace_gate('NOT1', gate.NOT, ('I1', 'I2'))
    expected.emplace_gate('OUT1', gate.AND, ('NOT1', 'AND1'))
    expected.emplace_gate('OUT2', gate.NOT, ('I4',))
    expected.set_outputs(['OUT1', 'OUT2'])

    expected_no_inputs = Circuit()
    expected_no_inputs.add_inputs(['I1', 'I2', 'I4'])
    expected_no_inputs.emplace_gate('AND1', gate.AND, ('I1', 'I2'))
    expected_no_inputs.emplace_gate('NOT1', gate.NOT, ('I1', 'I2'))
    expected_no_inputs.emplace_gate('OUT1', gate.AND, ('NOT1', 'AND1'))
    expected_no_inputs.emplace_gate('OUT2', gate.NOT, ('I4',))
    expected_no_inputs.set_outputs(['OUT1', 'OUT2'])

    simplified = remove_redundant_gates(original)
    assert simplified == expected
    simplified = remove_redundant_gates(original, allow_inputs_removal=True)
    assert simplified == expected_no_inputs


# Test case 1 for collapse_unary_operators:
#   - output collapses
#   - same outputs count as distinct.
#   - odd Not doesn't collapse
#   - even Not collapses (including LNOT, RNOT)
#   - any IFF collapses (including LIFF, RIFF)
#
original_circuit_1 = Circuit()
original_circuit_1.add_gate(Gate('input1', gate.INPUT))
original_circuit_1.add_gate(Gate('input2', gate.INPUT))
original_circuit_1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
original_circuit_1.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
original_circuit_1.emplace_gate('NOT1', gate.NOT, ('AND1',))
original_circuit_1.emplace_gate('NOT2', gate.NOT, ('NOT1',))
original_circuit_1.mark_as_output('NOT2')
original_circuit_1.emplace_gate('LNOT3', gate.LNOT, ('AND1', 'input1'))
original_circuit_1.emplace_gate(
    'RNOT4',
    gate.RNOT,
    (
        'input2',
        'LNOT3',
    ),
)
original_circuit_1.mark_as_output('RNOT4')
original_circuit_1.emplace_gate('NOT5', gate.NOT, ('AND1',))
original_circuit_1.mark_as_output('NOT5')
original_circuit_1.emplace_gate('IFF1', gate.IFF, ('AND2',))
original_circuit_1.emplace_gate('IFF2', gate.IFF, ('IFF1',))
original_circuit_1.mark_as_output('IFF2')
original_circuit_1.emplace_gate('LIFF3', gate.LIFF, ('AND2', 'input1'))
original_circuit_1.emplace_gate(
    'RIFF4',
    gate.RIFF,
    (
        'input2',
        'LIFF3',
    ),
)
original_circuit_1.mark_as_output('RIFF4')
original_circuit_1.emplace_gate('IFF5', gate.IFF, ('AND2',))
original_circuit_1.mark_as_output('IFF5')

expected_circuit_1 = Circuit()
expected_circuit_1.add_gate(Gate('input1', gate.INPUT))
expected_circuit_1.add_gate(Gate('input2', gate.INPUT))
expected_circuit_1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
expected_circuit_1.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
expected_circuit_1.mark_as_output('AND1')
expected_circuit_1.mark_as_output('AND1')
expected_circuit_1.emplace_gate('NOT5', gate.NOT, ('AND1',))
expected_circuit_1.mark_as_output('NOT5')
expected_circuit_1.mark_as_output('AND2')
expected_circuit_1.mark_as_output('AND2')
expected_circuit_1.mark_as_output('AND2')

# Test case 2 for collapse_unary_operators
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
def test_collapse_unary_gates(original_circuit: Circuit, expected_circuit: Circuit):
    simplified_circuit = remove_redundant_gates(
        collapse_unary_operators(original_circuit)
    )
    assert simplified_circuit == expected_circuit


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
def test_replace_equivalent_gates(original_circuit: Circuit, expected_circuit: Circuit):
    equivalent_groups = _find_equivalent_gates_groups(original_circuit)
    simplified_circuit = _replace_equivalent_gates(original_circuit, equivalent_groups)
    assert are_circuits_isomorphic(simplified_circuit, expected_circuit)


# Test case 1 for collapse_equivalent_gates_sparse
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
def test_collapse_equivalent_gates_sparse(
    original_circuit: Circuit, expected_circuit: Circuit
):
    simplified_circuit = collapse_equivalent_gates_sparse(original_circuit)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on collapse_equivalent_gates_sparse"


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
def test_remove_identities(original_circuit: Circuit, expected_circuit: Circuit):
    simplified_circuit = remove_identities(original_circuit)
    assert are_circuits_isomorphic(
        simplified_circuit, expected_circuit
    ), "Failed test on remove_identities"
