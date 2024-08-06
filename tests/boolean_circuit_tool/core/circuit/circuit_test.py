import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitGateIsAbsentError,
    CircuitValidationError,
    CreateBlockError,
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
    assert instance.size == 1
    assert instance.gates_number == 0
    assert instance.inputs == ['A']
    assert instance.input_size == 1
    assert instance.output_size == 0
    assert instance.outputs == []
    assert instance._gates.keys() == {'A'}

    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.size == 3
    assert instance.gates_number == 1
    assert instance.inputs == ['A']
    assert instance.outputs == ['C']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._gates.keys() == {'A', 'B', 'C'}
    assert instance.get_gate('A').label == 'A'
    assert instance.get_gate('A').gate_type == INPUT
    assert instance.get_gate('A').operands == ()

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == NOT
    assert instance.get_gate('B').operands == ('A',)

    assert instance.get_gate('C').label == 'C'
    assert instance.get_gate('C').gate_type == AND
    assert instance.get_gate('C').operands == ('A', 'B')

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('A', OR, ('B', 'C')))

    with pytest.raises(CircuitValidationError):
        instance.add_gate(Gate('D', OR, ('B', 'V')))

    instance.mark_as_output('A')
    instance.mark_as_output('C')
    instance.mark_as_output('A')
    assert instance.outputs == ['C', 'A', 'C', 'A']
    assert instance.output_size == 4
    assert instance.all_indexes_of_output('C') == [0, 2]
    assert instance.index_of_output('A') == 1

    assert instance.gates == {
        'A': Gate('A', INPUT, ()),
        'B': Gate('B', NOT, ('A',)),
        'C': Gate('C', AND, ('A', 'B')),
    }


def test_rename_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    instance.rename_gate('A', 'V')

    assert instance.size == 3
    assert instance.gates_number == 1
    assert instance.inputs == ['V']
    assert instance.outputs == ['C']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._gates.keys() == {'V', 'B', 'C'}
    assert instance.get_gate('V').label == 'V'
    assert instance.get_gate('V').gate_type == INPUT
    assert instance.get_gate('V').operands == ()

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == NOT
    assert instance.get_gate('B').operands == ('V',)

    assert instance.get_gate('C').label == 'C'
    assert instance.get_gate('C').gate_type == AND
    assert instance.get_gate('C').operands == ('V', 'B')

    with pytest.raises(CircuitGateIsAbsentError):
        instance.rename_gate('D', 'E')

    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('E', INPUT))
    instance.add_gate(Gate('F', INPUT))
    instance.mark_as_output('F')
    instance.mark_as_output('A')
    instance.mark_as_output('E')

    instance.rename_gate('A', 'V')
    assert instance.inputs == ['V', 'E', 'F']
    assert instance.outputs == ['F', 'V', 'E']


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


def test_block():
    C0 = Circuit()
    C0.add_gate(Gate('A', INPUT))
    C0.add_gate(Gate('B', INPUT))
    C0.add_gate(Gate('C', OR, ('A', 'B')))
    C0.mark_as_output('C')

    C1 = Circuit()
    C1.add_gate(Gate('A', INPUT))
    C1.add_gate(Gate('B', NOT, ('A',)))
    C1.add_gate(Gate('C', AND, ('A', 'B')))
    C1.add_gate(Gate('D', OR, ('A', 'B')))
    C1.mark_as_output('C')
    C1.mark_as_output('D')

    C2 = Circuit()
    C2.add_gate(Gate('A', INPUT))
    C2.add_gate(Gate('B', INPUT))
    C2.add_gate(Gate('C', AND, ('A', 'B')))
    C2.mark_as_output('C')

    C = Circuit()

    C.connect_block([], 'C0', C0)
    assert C.size == 3
    assert C.gates_number == 1
    assert C.inputs == ['C0@A', 'C0@B']
    assert C.outputs == ['C0@C']
    assert C._gates.keys() == {'C0@A', 'C0@B', 'C0@C'}
    assert C.get_gate('C0@C').gate_type == OR
    assert C.get_gate('C0@C').operands == ('C0@A', 'C0@B')

    C.make_block('backup_C0', C.inputs, C.outputs)
    C.connect_block(C.outputs, 'C1', C1)
    assert C.size == 6
    assert C.gates_number == 3
    assert C.inputs == ['C0@A', 'C0@B']
    assert C.outputs == ['C1@C', 'C1@D']
    assert C.get_block('backup_C0').outputs == ['C0@C']
    assert C._gates.keys() == {'C0@A', 'C0@B', 'C0@C', 'C1@B', 'C1@C', 'C1@D'}
    assert C.get_gate('C0@C').gate_type == OR
    assert C.get_gate('C0@C').operands == ('C0@A', 'C0@B')
    assert C.get_gate('C1@B').gate_type == NOT
    assert C.get_gate('C1@B').operands == ('C0@C',)
    assert C.get_gate('C1@C').gate_type == AND
    assert C.get_gate('C1@C').operands == ('C0@C', 'C1@B')
    assert C.get_gate_users('C0@C') == ['C1@B', 'C1@D', 'C1@C']

    C.make_block('backup_C0_C1', C.inputs, C.outputs)
    with pytest.raises(CreateBlockError):
        C.make_block('make_B1', C.inputs[1:], ['C1@C'])
    C.connect_block(C.outputs[1:], 'C2', C2)
    assert C.size == 8
    assert C.gates_number == 4
    assert C.inputs == ['C0@A', 'C0@B', 'C2@B']
    assert C.outputs == ['C1@C', 'C2@C']
    assert C._gates.keys() == {
        'C0@A',
        'C0@B',
        'C0@C',
        'C1@B',
        'C1@C',
        'C1@D',
        'C2@B',
        'C2@C',
    }
    C.make_block('make_B1', C.inputs[:2], ['C1@C'])

    C2.connect_block(C2.outputs, 'C', C)
    assert C2.size == 10
    assert C2.gates_number == 5
    assert C2.inputs == ['A', 'B', 'C@C0@B', 'C@C2@B']
    assert C2.outputs == ['C@C1@C', 'C@C2@C']
    assert C2.input_size == 4
    assert C2.output_size == 2

    assert C2.get_gate('A').label == 'A'
    assert C2.get_gate('A').gate_type == INPUT
    assert C2.get_gate('A').operands == ()
    assert C2.get_gate_users('A') == ['C']

    assert C2.get_gate('B').label == 'B'
    assert C2.get_gate('B').gate_type == INPUT
    assert C2.get_gate('B').operands == ()
    assert C2.get_gate_users('B') == ['C']

    assert C2.get_gate('C').label == 'C'
    assert C2.get_gate('C').gate_type == AND
    assert C2.get_gate('C').operands == ('A', 'B')
    assert C2.get_gate_users('C') == ['C@C0@C']

    assert C2.get_gate('C@C0@B').label == 'C@C0@B'
    assert C2.get_gate('C@C0@B').gate_type == INPUT
    assert C2.get_gate('C@C0@B').operands == ()
    assert C2.get_gate_users('C@C0@B') == ['C@C0@C']

    assert C2.get_gate('C@C2@B').label == 'C@C2@B'
    assert C2.get_gate('C@C2@B').gate_type == INPUT
    assert C2.get_gate('C@C2@B').operands == ()
    assert C2.get_gate_users('C@C2@B') == ['C@C2@C']

    assert C2.get_gate('C@C0@C').label == 'C@C0@C'
    assert C2.get_gate('C@C0@C').gate_type == OR
    assert C2.get_gate('C@C0@C').operands == ('C', 'C@C0@B')
    assert C2.get_gate_users('C@C0@C') == ['C@C1@B', 'C@C1@C', 'C@C1@D']

    assert C2.get_gate('C@C1@B').label == 'C@C1@B'
    assert C2.get_gate('C@C1@B').gate_type == NOT
    assert C2.get_gate('C@C1@B').operands == ('C@C0@C',)
    assert C2.get_gate_users('C@C1@B') == ['C@C1@C', 'C@C1@D']

    assert C2.get_gate('C@C1@C').label == 'C@C1@C'
    assert C2.get_gate('C@C1@C').gate_type == AND
    assert C2.get_gate('C@C1@C').operands == ('C@C0@C', 'C@C1@B')
    assert C2.get_gate_users('C@C1@C') == []

    assert C2.get_gate('C@C1@D').label == 'C@C1@D'
    assert C2.get_gate('C@C1@D').gate_type == OR
    assert C2.get_gate('C@C1@D').operands == ('C@C0@C', 'C@C1@B')
    assert C2.get_gate_users('C@C1@D') == ['C@C2@C']

    assert C2.get_gate('C@C2@C').label == 'C@C2@C'
    assert C2.get_gate('C@C2@C').gate_type == AND
    assert C2.get_gate('C@C2@C').operands == ('C@C1@D', 'C@C2@B')
    assert C2.get_gate_users('C@C2@C') == []

    assert list(C2.blocks.keys()) == [
        'C',
        'C@C0',
        'C@backup_C0',
        'C@C1',
        'C@backup_C0_C1',
        'C@C2',
        'C@make_B1',
    ]
    assert C2.get_block('C@C0').inputs == ['C', 'C@C0@B']
    assert C2.get_block('C@C0').gates == ['C@C0@C']
    assert C2.get_block('C@C0').outputs == ['C@C0@C']


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

    instance.mark_as_output('C')
    assert instance.evaluate([True]) == [False, False]

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

    instance.mark_as_output('C')
    assert instance.get_truth_table() == [
        [False, False, False, True],
        [False, True, False, True],
        [False, False, False, True],
    ]


def test_circuit_gate():
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.emplace_gate('C', AND, ('A', 'B'))
    instance.mark_as_output('C')

    assert instance.size == 3
    assert instance.gates_number == 1
    assert instance.inputs == ['A']
    assert instance.outputs == ['C']
    assert instance.input_size == 1
    assert instance.output_size == 1

    assert instance._gates.keys() == {'A', 'B', 'C'}
    assert instance.get_gate('A').label == 'A'
    assert instance.get_gate('A').gate_type == INPUT
    assert instance.get_gate('A').operands == ()
    assert instance.get_gate_users('A') == ['B', 'C']

    assert instance.get_gate('B').label == 'B'
    assert instance.get_gate('B').gate_type == NOT
    assert instance.get_gate('B').operands == ('A',)
    assert instance.get_gate_users('B') == ['C']

    assert instance.get_gate('C').label == 'C'
    assert instance.get_gate('C').gate_type == AND
    assert instance.get_gate('C').operands == ('A', 'B')
    assert instance.get_gate_users('C') == []

    assert instance.has_gate('A') == True
    assert instance.has_gate('D') == False
