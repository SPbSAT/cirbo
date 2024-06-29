import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import Gate, GateType
from boolean_circuit_tool.core.circuit.operators import GateAssign


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

    assert instance.evaluate_circuit({'A': GateAssign.TRUE}) == GateAssign.FALSE
    assert instance.evaluate_circuit({'A': GateAssign.FALSE}) == GateAssign.FALSE
    assert (
        instance.evaluate_circuit({'A': GateAssign.UNDEFINED}) == GateAssign.UNDEFINED
    )

    instance = Circuit()

    instance.add_gate(Gate('A', GateType.INPUT))
    instance.add_gate(Gate('B', GateType.INPUT))
    instance.add_gate(Gate('C', GateType.NOT, ('A',)))
    instance.add_gate(Gate('D', GateType.OR, ('A', 'B')))
    instance.add_gate(Gate('E', GateType.XOR, ('A', 'B')))
    instance.add_gate(Gate('F', GateType.AND, ('B', 'D')))
    instance.mark_as_output('D')
    instance.mark_as_output('E')
    instance.mark_as_output('F')

    assert (
        instance.evaluate_circuit({'A': GateAssign.FALSE, 'B': GateAssign.FALSE})
        == GateAssign.FALSE
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.FALSE, 'B': GateAssign.TRUE})
        == GateAssign.TRUE
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.FALSE, 'B': GateAssign.UNDEFINED})
        == GateAssign.UNDEFINED
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.TRUE, 'B': GateAssign.FALSE})
        == GateAssign.FALSE
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.TRUE, 'B': GateAssign.TRUE})
        == GateAssign.FALSE
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.TRUE, 'B': GateAssign.UNDEFINED})
        == GateAssign.UNDEFINED
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.UNDEFINED, 'B': GateAssign.FALSE})
        == GateAssign.FALSE
    )
    assert (
        instance.evaluate_circuit({'A': GateAssign.UNDEFINED, 'B': GateAssign.TRUE})
        == GateAssign.UNDEFINED
    )
    assert (
        instance.evaluate_circuit(
            {'A': GateAssign.UNDEFINED, 'B': GateAssign.UNDEFINED}
        )
        == GateAssign.UNDEFINED
    )
