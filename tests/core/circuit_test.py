from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.exceptions import CircuitValidationError
from boolean_circuit_tool.core.gate import Gate, GateType

def test_circuit():

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    assert instance.gates_number == 1
    assert instance.input_gates == {'A'}
    assert instance.output_gates == set()
    assert instance.gates == {}

    instance.add_gate(Gate('B', GateType.NOT, ('A',)))
    instance.add_gate(Gate('C', GateType.AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.gates_number == 3
    assert instance.input_gates == {'A'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'B', 'C'}
    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('A',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('A', 'B')

    try:
        instance.add_gate(Gate('A', GateType.OR, ('B', 'C')))
        assert False
    except CircuitValidationError:
        assert True

    try:
        instance.add_gate(Gate('D', GateType.OR, ('B', 'V')))
        assert False
    except CircuitValidationError:
        assert True

    instance.rename_gate('A', 'V')

    assert instance.gates_number == 3
    assert instance.input_gates == {'V'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'B', 'C'}
    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('V',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('V', 'B')