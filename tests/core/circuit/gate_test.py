from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import AND, Gate, INPUT, NOT


def test_gate_capabilities():
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.emplace_gate('C', AND, ('A', 'B'))
    instance.mark_as_output('C')

    assert instance.elements_number == 3
    assert instance.inputs == ['A']
    assert instance.outputs == ['C']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._elements.keys() == {'A', 'B', 'C'}
    assert instance.get_element('A').label == 'A'
    assert instance.get_element('A').gate_type == INPUT
    assert instance.get_element('A').operands == ()
    assert instance.get_element_users('A') == ['B', 'C']

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == NOT
    assert instance.get_element('B').operands == ('A',)
    assert instance.get_element_users('B') == ['C']

    assert instance.get_element('C').label == 'C'
    assert instance.get_element('C').gate_type == AND
    assert instance.get_element('C').operands == ('A', 'B')
    assert instance.get_element_users('C') == []

    assert instance.has_element('A') == True
    assert instance.has_element('D') == False
