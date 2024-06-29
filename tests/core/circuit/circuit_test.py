import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import Gate, GateType


def test_create_circuit():

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    assert instance.gates_number == 1
    assert instance.input_gates == {'A'}
    assert instance.output_gates == set()
    assert instance.gates.keys() == {'A'}

    instance.add_gate(Gate('B', GateType.NOT, ('A',)))
    instance.add_gate(Gate('C', GateType.AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.gates_number == 3
    assert instance.input_gates == {'A'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'A', 'B', 'C'}
    assert instance.gates['A'].label == 'A'
    assert instance.gates['A'].gate_type == GateType.INPUT
    assert tuple(instance.gates['A'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('A',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('A', 'B')

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('A', GateType.OR, ('B', 'C')))

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('D', GateType.OR, ('B', 'V')))


def test_rename_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    instance.add_gate(Gate('B', GateType.NOT, ('A',)))
    instance.add_gate(Gate('C', GateType.AND, ('A', 'B')))
    instance.mark_as_output('C')

    instance.rename_gate('A', 'V')

    assert instance.gates_number == 3
    assert instance.input_gates == {'V'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'V', 'B', 'C'}
    assert instance.gates['V'].label == 'V'
    assert instance.gates['V'].gate_type == GateType.INPUT
    assert tuple(instance.gates['V'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('V',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('V', 'B')

    instance.rename_gate('D', 'E')

    assert instance.gates_number == 3
    assert instance.input_gates == {'V'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'V', 'B', 'C'}
    assert instance.gates['V'].label == 'V'
    assert instance.gates['V'].gate_type == GateType.INPUT
    assert tuple(instance.gates['V'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('V',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('V', 'B')


def test_evaluate_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    instance.add_gate(Gate('B', GateType.NOT, ('A',)))
    instance.add_gate(Gate('C', GateType.AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.evaluate_circuit({'A': True}) == False
    assert instance.evaluate_circuit({'A': False}) == False

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    instance.add_gate(Gate('B', GateType.INPUT))
    instance.add_gate(Gate('C', GateType.NOT, ('A',)))
    instance.add_gate(Gate('D', GateType.OR, ('A', 'B')))
    instance.add_gate(Gate('E', GateType.XOR, ('A', 'C')))
    instance.add_gate(Gate('F', GateType.AND, ('B', 'C')))
    instance.mark_as_output('D')
    instance.mark_as_output('E')
    instance.mark_as_output('F')

    assert instance.evaluate_circuit({'A': True, 'B': True}) == False
    assert instance.evaluate_circuit({'A': False, 'B': True}) == True
    assert instance.evaluate_circuit({'A': True, 'B': False}) == False
    assert instance.evaluate_circuit({'A': False, 'B': False}) == False

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    instance.add_gate(Gate('B', GateType.INPUT))
    instance.add_gate(Gate('C', GateType.AND, ('A', 'B')))
    instance.add_gate(Gate('D', GateType.OR, ('A', 'C')))
    instance.add_gate(Gate('E', GateType.OR, ('C', 'D')))
    instance.mark_as_output('E')

    assert instance.evaluate_circuit({'A': True, 'B': True}) == True
    assert instance.evaluate_circuit({'A': False, 'B': True}) == False
    assert instance.evaluate_circuit({'A': True, 'B': False}) == True
    assert instance.evaluate_circuit({'A': False, 'B': False}) == False
