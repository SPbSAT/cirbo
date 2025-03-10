import pytest

from cirbo.core.circuit import Circuit, Gate, gate
from cirbo.minimization.simplification import MergeUnaryOperators


# Test case 1 for MergeUnaryOperators:
#   - output merges
#   - same outputs count as distinct.
#   - odd Not doesn't merge
#   - even Not merges (including LNOT, RNOT)
#   - any IFF merges (including LIFF, RIFF)
#
original_circuit_1 = Circuit()
original_circuit_1.add_gate(Gate('input1', gate.INPUT))
original_circuit_1.add_gate(Gate('input2', gate.INPUT))
original_circuit_1.add_gate(Gate('input3', gate.INPUT))
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
expected_circuit_1.add_gate(Gate('input3', gate.INPUT))
expected_circuit_1.emplace_gate('AND1', gate.AND, ('input1', 'input2'))
expected_circuit_1.emplace_gate('AND2', gate.AND, ('input1', 'input2'))
expected_circuit_1.mark_as_output('AND1')
expected_circuit_1.mark_as_output('AND1')
expected_circuit_1.emplace_gate('NOT5', gate.NOT, ('AND1',))
expected_circuit_1.mark_as_output('NOT5')
expected_circuit_1.mark_as_output('AND2')
expected_circuit_1.mark_as_output('AND2')
expected_circuit_1.mark_as_output('AND2')

# Test case 2 for MergeUnaryOperators
original_circuit_2 = Circuit()
original_circuit_2.add_gate(Gate('input1', gate.INPUT))
original_circuit_2.add_gate(Gate('input2', gate.INPUT))
original_circuit_2.add_gate(Gate('input3', gate.INPUT))
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
expected_circuit_2.add_gate(Gate('input3', gate.INPUT))
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
def test_merge_unary_gates(original_circuit: Circuit, expected_circuit: Circuit):
    simplified_circuit = MergeUnaryOperators().transform(original_circuit)
    assert simplified_circuit == expected_circuit
