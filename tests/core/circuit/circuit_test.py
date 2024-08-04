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
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined


def test_create_circuit():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    assert instance.elements_number == 1
    assert instance.inputs == ['A']
    assert instance.input_size == 1
    assert instance.output_size == 0
    assert instance.outputs == []
    assert instance._elements.keys() == {'A'}

    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
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

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == NOT
    assert instance.get_element('B').operands == ('A',)

    assert instance.get_element('C').label == 'C'
    assert instance.get_element('C').gate_type == AND
    assert instance.get_element('C').operands == ('A', 'B')

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
    assert instance.inputs == ['V']
    assert instance.outputs == ['C']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._elements.keys() == {'V', 'B', 'C'}
    assert instance.get_element('V').label == 'V'
    assert instance.get_element('V').gate_type == INPUT
    assert instance.get_element('V').operands == ()

    assert instance.get_element('B').label == 'B'
    assert instance.get_element('B').gate_type == NOT
    assert instance.get_element('B').operands == ('V',)

    assert instance.get_element('C').label == 'C'
    assert instance.get_element('C').gate_type == AND
    assert instance.get_element('C').operands == ('V', 'B')

    with pytest.raises(CircuitElementIsAbsentError):
        instance.rename_element('D', 'E')


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

    assert instance.evaluate_circuit_outputs({'1': arg1, '2': arg2}) == {'14': result}


def test_evaluate_circuit():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.evaluate_circuit_outputs({'A': True}) == {'C': False}
    assert instance.evaluate_circuit_outputs({'A': False}) == {'C': False}
    assert instance.evaluate_circuit_outputs({'A': Undefined}) == {'C': Undefined}
    assert instance.evaluate_circuit({'A': True}) == {'A': True, 'B': False, 'C': False}
    assert instance.evaluate_circuit({'A': False}) == {
        'A': False,
        'B': True,
        'C': False,
    }
    assert instance.evaluate_circuit({'A': Undefined}) == {
        'A': Undefined,
        'B': Undefined,
        'C': Undefined,
    }

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

    assert instance.evaluate_circuit_outputs({'A': False, 'B': False}) == {
        'D': False,
        'E': False,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': False, 'B': False}) == {
        'A': False,
        'B': False,
        'C': Undefined,
        'D': False,
        'E': False,
        'F': False,
    }
    assert instance.evaluate_circuit_outputs({'A': False, 'B': True}) == {
        'D': True,
        'E': True,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': False, 'B': True}) == {
        'A': False,
        'B': True,
        'C': Undefined,
        'D': True,
        'E': True,
        'F': True,
    }
    assert instance.evaluate_circuit_outputs({'A': False, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit({'A': False, 'B': Undefined}) == {
        'A': False,
        'B': Undefined,
        'C': Undefined,
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit_outputs({'A': True, 'B': False}) == {
        'D': True,
        'E': True,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': True, 'B': False}) == {
        'A': True,
        'B': False,
        'C': Undefined,
        'D': True,
        'E': True,
        'F': False,
    }
    assert instance.evaluate_circuit_outputs({'A': True, 'B': True}) == {
        'D': True,
        'E': False,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': True, 'B': True}) == {
        'A': True,
        'B': True,
        'C': Undefined,
        'D': True,
        'E': False,
        'F': True,
    }
    assert instance.evaluate_circuit_outputs({'A': True, 'B': Undefined}) == {
        'D': True,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit({'A': True, 'B': Undefined}) == {
        'A': True,
        'B': Undefined,
        'C': Undefined,
        'D': True,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit_outputs({'A': Undefined, 'B': False}) == {
        'D': Undefined,
        'E': Undefined,
        'F': False,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': False}) == {
        'A': Undefined,
        'B': False,
        'C': Undefined,
        'D': Undefined,
        'E': Undefined,
        'F': False,
    }
    assert instance.evaluate_circuit_outputs({'A': Undefined, 'B': True}) == {
        'D': True,
        'E': Undefined,
        'F': True,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': True}) == {
        'A': Undefined,
        'B': True,
        'C': Undefined,
        'D': True,
        'E': Undefined,
        'F': True,
    }
    assert instance.evaluate_circuit_outputs({'A': Undefined, 'B': Undefined}) == {
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }
    assert instance.evaluate_circuit({'A': Undefined, 'B': Undefined}) == {
        'A': Undefined,
        'B': Undefined,
        'C': Undefined,
        'D': Undefined,
        'E': Undefined,
        'F': Undefined,
    }


def test_evaluate():

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

    assert instance.evaluate([False, False]) == [False, False, False]
    assert instance.evaluate([False, True]) == [True, True, True]
    assert instance.evaluate([False, Undefined]) == [Undefined, Undefined, Undefined]
    assert instance.evaluate([True, False]) == [True, True, False]
    assert instance.evaluate([True, True]) == [True, False, True]
    assert instance.evaluate([True, Undefined]) == [True, Undefined, Undefined]
    assert instance.evaluate([Undefined, False]) == [Undefined, Undefined, False]
    assert instance.evaluate([Undefined, False]) == [Undefined, Undefined, False]
    assert instance.evaluate([Undefined, True]) == [True, Undefined, True]
    assert instance.evaluate([Undefined, Undefined]) == [
        Undefined,
        Undefined,
        Undefined,
    ]


def test_evaluate_at():

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

    assert instance.evaluate_at([False, False], 0) == False
    assert instance.evaluate_at([False, False], 1) == False
    assert instance.evaluate_at([False, False], 2) == False
    assert instance.evaluate_at([False, True], 0) == True
    assert instance.evaluate_at([False, True], 1) == True
    assert instance.evaluate_at([False, True], 2) == True
    assert instance.evaluate_at([False, Undefined], 0) == Undefined
    assert instance.evaluate_at([False, Undefined], 1) == Undefined
    assert instance.evaluate_at([False, Undefined], 2) == Undefined
    assert instance.evaluate_at([True, False], 0) == True
    assert instance.evaluate_at([True, False], 1) == True
    assert instance.evaluate_at([True, False], 2) == False
    assert instance.evaluate_at([True, True], 0) == True
    assert instance.evaluate_at([True, True], 1) == False
    assert instance.evaluate_at([True, True], 2) == True
    assert instance.evaluate_at([True, Undefined], 0) == True
    assert instance.evaluate_at([True, Undefined], 1) == Undefined
    assert instance.evaluate_at([True, Undefined], 2) == Undefined
    assert instance.evaluate_at([Undefined, False], 0) == Undefined
    assert instance.evaluate_at([Undefined, False], 1) == Undefined
    assert instance.evaluate_at([Undefined, False], 2) == False
    assert instance.evaluate_at([Undefined, False], 0) == Undefined
    assert instance.evaluate_at([Undefined, False], 1) == Undefined
    assert instance.evaluate_at([Undefined, False], 2) == False
    assert instance.evaluate_at([Undefined, True], 0) == True
    assert instance.evaluate_at([Undefined, True], 1) == Undefined
    assert instance.evaluate_at([Undefined, True], 2) == True
    assert instance.evaluate_at([Undefined, Undefined], 0) == Undefined
    assert instance.evaluate_at([Undefined, Undefined], 1) == Undefined
    assert instance.evaluate_at([Undefined, Undefined], 2) == Undefined


def test_is_constant():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.is_constant() == True

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('D')

    assert instance.is_constant() == False


def test_is_constant_at():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', NOT, ('A',)))
    instance.add_gate(Gate('D', AND, ('A', 'C')))
    instance.add_gate(Gate('E', AND, ('A', 'B')))
    instance.add_gate(Gate('F', OR, ('E', 'B')))
    instance.mark_as_output('D')
    instance.mark_as_output('F')

    assert instance.is_constant() == False
    assert instance.is_constant_at(0) == True
    assert instance.is_constant_at(1) == False


def test_is_monotonic():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.is_monotonic(inverse=False) == True
    assert instance.is_monotonic(inverse=True) == False

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.is_monotonic(inverse=False) == True
    assert instance.is_monotonic(inverse=True) == True

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('D')

    assert instance.is_monotonic(inverse=False) == False
    assert instance.is_monotonic(inverse=True) == False


def test_is_monotonic_at():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', AND, ('A', 'D')))
    instance.mark_as_output('C')
    instance.mark_as_output('E')

    assert instance.is_monotonic(inverse=False) == True
    assert instance.is_monotonic(inverse=True) == False
    assert instance.is_monotonic_at(0, inverse=False) == True
    assert instance.is_monotonic_at(0, inverse=True) == True
    assert instance.is_monotonic_at(1, inverse=False) == True
    assert instance.is_monotonic_at(1, inverse=True) == False

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', AND, ('A', 'D')))
    instance.add_gate(Gate('F', AND, ('A', 'D')))
    instance.add_gate(Gate('G', OR, ('F', 'D')))
    instance.mark_as_output('C')
    instance.mark_as_output('E')
    instance.mark_as_output('G')

    assert instance.is_monotonic(inverse=False) == False
    assert instance.is_monotonic(inverse=True) == False
    assert instance.is_monotonic_at(0, inverse=False) == True
    assert instance.is_monotonic_at(0, inverse=True) == True
    assert instance.is_monotonic_at(1, inverse=False) == True
    assert instance.is_monotonic_at(1, inverse=True) == False
    assert instance.is_monotonic_at(2, inverse=False) == False
    assert instance.is_monotonic_at(2, inverse=True) == False


def test_is_symmetric():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', AND, ('C', 'D')))
    instance.mark_as_output('E')

    assert instance.is_symmetric() == True

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', OR, ('C', 'D')))
    instance.mark_as_output('E')

    assert instance.is_symmetric() == False


def test_is_symmetric_at():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', AND, ('C', 'D')))
    instance.add_gate(Gate('F', OR, ('C', 'D')))
    instance.mark_as_output('E')
    instance.mark_as_output('F')

    assert instance.is_symmetric() == False
    assert instance.is_symmetric_at(0) == True
    assert instance.is_symmetric_at(1) == False


def test_is_dependent_on_input_at():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.is_dependent_on_input_at(0, 0) == True
    assert instance.is_dependent_on_input_at(0, 1) == True

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.is_dependent_on_input_at(0, 0) == False


def test_is_output_equal_to_input():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', OR, ('C', 'D')))
    instance.mark_as_output('E')
    instance.mark_as_output('B')

    assert instance.is_output_equal_to_input(0, 0) == False
    assert instance.is_output_equal_to_input(0, 1) == True
    assert instance.is_output_equal_to_input(1, 0) == False
    assert instance.is_output_equal_to_input(1, 1) == False


def test_is_output_equal_to_input_negation():
    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('D')
    instance.mark_as_output('C')

    assert instance.is_output_equal_to_input_negation(0, 0) == True
    assert instance.is_output_equal_to_input_negation(1, 0) == False


def test_get_significant_inputs_of():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('D')
    instance.mark_as_output('C')

    assert instance.get_significant_inputs_of(0) == [0]
    assert instance.get_significant_inputs_of(1) == []


def test_find_negations_to_make_symmetric():

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', NOT, ('B',)))
    instance.add_gate(Gate('D', OR, ('A', 'C')))
    instance.mark_as_output('D')

    assert instance.is_symmetric() == False
    assert instance.find_negations_to_make_symmetric([0]) == [False, True]


def test_get_truth_table():
    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('C')
    instance.mark_as_output('D')

    assert instance.get_truth_table() == [
        [False, False, False, True],
        [False, True, False, True],
    ]


def test_circuit_element():
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