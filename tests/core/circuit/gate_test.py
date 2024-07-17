from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import AND, and_, Gate, INPUT, NOT


def test_gate_capabilities():
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.emplace_gate('C', AND, ('A', 'B'))
    instance.mark_as_output('C')

    my_gate = instance.get_element('C')

    assert my_gate.label == 'C'
    assert my_gate.gate_type == AND
    assert my_gate.operands == ('A', 'B')
    assert my_gate.operator == and_
    assert my_gate.format_gate() == 'C = AND(A, B)'
    assert str(my_gate) == "Gate(C, AND, ('A', 'B'))"
