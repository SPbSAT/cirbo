from cirbo.core.circuit import Circuit, gate
from cirbo.minimization.simplification import RemoveRedundantGates


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

    simplified = RemoveRedundantGates().transform(original)
    assert simplified == expected
    simplified = RemoveRedundantGates(allow_inputs_removal=True).transform(original)
    assert simplified == expected_no_inputs
