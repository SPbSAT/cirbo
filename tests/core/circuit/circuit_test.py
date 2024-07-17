import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitElementIsAbsentError,
    CircuitValidationError,
)
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Gate,
    GEQ,
    GT,
    INPUT,
    LEQ,
    LNOT,
    LT,
    NOT,
    OR,
    RNOT,
    XOR,
)
from boolean_circuit_tool.core.circuit.operators import (
    GateState,
    Undefined,
)


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
    assert instance._elements['A'].operands == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert instance._elements['B'].operands == ('A',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert instance._elements['C'].operands == ('A', 'B')

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
    assert instance._elements['V'].operands == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert instance._elements['B'].operands == ('V',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert instance._elements['C'].operands == ('V', 'B')

    with pytest.raises(CircuitElementIsAbsentError):
        instance.rename_element('D', 'E')


def test_evaluate_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.evaluate_circuit({'A': True}) == {'C': False}
    assert instance.evaluate_circuit({'A': False}) == {'C': False}
    assert instance.evaluate_circuit({'A': Undefined}) == {'C': Undefined}

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

    assert instance.evaluate_circuit({'A': False, 'B': False}) == {
        'D': False,
        'E': False,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': False, 'B': True}) == {
        'D': True,
        'E': True,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': False, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit({'A': True, 'B': False}) == {
        'D': True,
        'E': True,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': True, 'B': True}) == {
        'D': True,
        'E': False,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': True, 'B': Undefined}) == {
        'D': True,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': False}) == {
        'D': Undefined,
        'E': Undefined,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': True}) == {
        'D': True,
        'E': Undefined,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (True, False, False),
        (True, Undefined, Undefined),
        (False, True, False),
        (False, False, True),
        (False, Undefined, Undefined),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_spec_binary_gates(arg1: GateState, arg2: GateState, result: GateState):

    instance = Circuit()

    instance.add_gate(Gate('1', INPUT))
    instance.add_gate(Gate('2', INPUT))
    instance.add_gate(Gate('3', NOT, ('1',)))
    instance.add_gate(Gate('4', AND, ('1', '2')))
    instance.add_gate(Gate('5', XOR, ('1', '2')))
    instance.add_gate(Gate('6', AND, ('2', '4')))
    instance.add_gate(Gate('7', ALWAYS_FALSE))
    instance.add_gate(Gate('8', ALWAYS_TRUE, ('1',)))
    instance.add_gate(Gate('9', LNOT, ('7', '3')))
    instance.add_gate(Gate('10', RNOT, ('4', '8')))
    instance.add_gate(Gate('11', LEQ, ('2', '4')))
    instance.add_gate(Gate('12', LT, ('2', '11')))
    instance.add_gate(Gate('13', GEQ, ('11', '12')))
    instance.add_gate(Gate('14', GT, ('13', '5')))

    instance.mark_as_output('14')

    assert instance.evaluate_circuit({'1': arg1, '2': arg2}) == {'14': result}
