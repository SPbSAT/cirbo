from cirbo.core.circuit.gate import AND, and_, Gate


def test_gate_capabilities():
    my_gate = Gate('C', AND, ('A', 'B'))

    assert my_gate.label == 'C'
    assert my_gate.gate_type == AND
    assert my_gate.operands == ('A', 'B')
    assert my_gate.operator == and_
    assert my_gate.format_gate() == 'C = AND(A, B)'
    assert str(my_gate) == "Gate(C, AND, ('A', 'B'))"
