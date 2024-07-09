import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import AND, Gate, INPUT, NOT, OR, XOR
from boolean_circuit_tool.core.circuit.operators import Undefined


def test_create_circuit():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    assert instance.elements_number == 1
    assert instance._inputs == ['A']
    assert instance._outputs == []
    assert instance._elements.keys() == {'A'}

    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.elements_number == 3
    assert instance._inputs == ['A']
    assert instance._outputs == ['C']

    assert instance._elements.keys() == {'A', 'B', 'C'}
    assert instance._elements['A'].label == 'A'
    assert instance._elements['A'].gate_type == INPUT
    assert tuple(instance._elements['A'].operands) == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert tuple(instance._elements['B'].operands) == ('A',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert tuple(instance._elements['C'].operands) == ('A', 'B')

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('A', OR, ('B', 'C')))

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('D', OR, ('B', 'V')))


def test_rename_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    instance.rename_element('A', 'V')

    assert instance.elements_number == 3
    assert instance._inputs == ['V']
    assert instance._outputs == ['C']

    assert instance._elements.keys() == {'V', 'B', 'C'}
    assert instance._elements['V'].label == 'V'
    assert instance._elements['V'].gate_type == INPUT
    assert tuple(instance._elements['V'].operands) == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert tuple(instance._elements['B'].operands) == ('V',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert tuple(instance._elements['C'].operands) == ('V', 'B')

    instance.rename_element('D', 'E')

    assert instance.elements_number == 3
    assert instance._inputs == ['V']
    assert instance._outputs == ['C']

    assert instance._elements.keys() == {'V', 'B', 'C'}
    assert instance._elements['V'].label == 'V'
    assert instance._elements['V'].gate_type == INPUT
    assert tuple(instance._elements['V'].operands) == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert tuple(instance._elements['B'].operands) == ('V',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert tuple(instance._elements['C'].operands) == ('V', 'B')


def test_evaluate_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.evaluate({'A': True}) == {'C': False}
    assert instance.evaluate({'A': False}) == {'C': False}
    assert instance.evaluate({'A': Undefined}) == {'C': Undefined}

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', NOT, ('A',)))
    instance.add_gate(Gate('D', OR, ('A', 'B')))
    instance.add_gate(Gate('E', XOR, ('A', 'B')))
    instance.add_gate(Gate('F', AND, ('B', 'D')))
    instance.mark_as_output('D')
    instance.mark_as_output('E')
    instance.mark_as_output('F')

    assert instance.evaluate({'A': False, 'B': False}) == {
        'D': False,
        'E': False,
        'F': False,
    }
    assert instance.evaluate({'A': False, 'B': True}) == {
        'D': True,
        'E': True,
        'F': True,
    }
    assert instance.evaluate({'A': False, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate({'A': True, 'B': False}) == {
        'D': True,
        'E': True,
        'F': False,
    }
    assert instance.evaluate({'A': True, 'B': True}) == {
        'D': True,
        'E': False,
        'F': True,
    }
    assert instance.evaluate({'A': True, 'B': Undefined}) == {
        'D': True,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate({'A': Undefined, 'B': False}) == {
        'D': Undefined,
        'E': Undefined,
        'F': False,
    }
    assert instance.evaluate({'A': Undefined, 'B': True}) == {
        'D': True,
        'E': Undefined,
        'F': True,
    }
    assert instance.evaluate({'A': Undefined, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
