import copy

import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitGateIsAbsentError,
    CircuitValidationError,
    CreateBlockError,
    GateDoesntExistError,
    GateHasUsersError,
    GateNotInputError,
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
    assert instance.gates_number() == 0
    assert instance.inputs == ['A']
    assert instance.input_size == 1
    assert instance.output_size == 0
    assert instance.outputs == []
    assert instance._gates.keys() == {'A'}

    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    assert instance.size == 3
    assert instance.gates_number() == 1
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

    with pytest.raises(GateHasUsersError):
        instance.remove_gate('A')

    instance.remove_gate('C')
    assert instance.size == 2
    assert instance.gates_number() == 0
    assert instance.inputs == ['A']
    assert instance.outputs == ['A', 'A']
    assert instance.input_size == 1
    assert instance.output_size == 2
    assert instance.gates == {
        'A': Gate('A', INPUT, ()),
        'B': Gate('B', NOT, ('A',)),
    }
    assert instance.get_gate_users('A') == ['B']
    assert instance.get_gate_users('B') == []

    instance.remove_gate('B')
    assert instance.size == 1
    assert instance.gates_number() == 0
    assert instance.inputs == ['A']
    assert instance.outputs == ['A', 'A']
    assert instance.input_size == 1
    assert instance.output_size == 2
    assert instance.gates == {
        'A': Gate('A', INPUT, ()),
    }
    assert instance.get_gate_users('A') == []

    instance.remove_gate('A')
    assert instance.size == 0
    assert instance.gates_number() == 0
    assert instance.inputs == []
    assert instance.outputs == []
    assert instance.input_size == 0
    assert instance.output_size == 0
    assert instance.gates == {}


def test_find_inputs_outputs():
    instance = Circuit()
    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.add_gate(Gate('D', OR, ('C', 'B')))
    instance.mark_as_output('C')
    instance.mark_as_output('D')
    instance.mark_as_output('C')

    assert instance.input_at_index(0) == 'A'
    assert instance.input_at_index(1) == 'B'
    assert instance.output_at_index(0) == 'C'
    assert instance.output_at_index(1) == 'D'
    assert instance.output_at_index(2) == 'C'
    assert instance.all_indexes_of_output('C') == [0, 2]
    assert instance.all_indexes_of_output('D') == [1]
    assert instance.index_of_input('A') == 0
    assert instance.index_of_input('B') == 1
    assert instance.index_of_output('C') == 0
    assert instance.index_of_output('D') == 1
    with pytest.raises(GateDoesntExistError):
        instance.index_of_input('V')
    with pytest.raises(GateDoesntExistError):
        instance.index_of_input('C')
    with pytest.raises(GateDoesntExistError):
        instance.index_of_output('V')
    with pytest.raises(GateDoesntExistError):
        instance.input_at_index(2)
    with pytest.raises(GateDoesntExistError):
        instance.output_at_index(3)


def test_rename_gate():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', NOT, ('A',)))
    instance.add_gate(Gate('C', AND, ('A', 'B')))
    instance.mark_as_output('C')

    instance.rename_gate('A', 'V')

    assert instance.size == 3
    assert instance.gates_number() == 1
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
    C1.add_gate(Gate('B', INPUT))
    C1.add_gate(Gate('C', AND, ('A', 'B')))
    C1.mark_as_output('C')

    C2 = Circuit()
    C2.add_gate(Gate('A', INPUT))
    C2.add_gate(Gate('B', INPUT))
    C2.add_gate(Gate('C', INPUT))
    C2.add_gate(Gate('D', OR, ('A', 'B')))
    C2.add_gate(Gate('E', AND, ('C', 'D')))
    C2.add_gate(Gate('F', AND, ('D', 'E')))
    C2.mark_as_output('F')

    C3 = Circuit()
    C3.add_gate(Gate('A', INPUT))
    C3.add_gate(Gate('B', INPUT))
    C3.add_gate(Gate('C', INPUT))
    C3.add_gate(Gate('D', OR, ('A', 'B')))
    C3.add_gate(Gate('E', AND, ('C', 'D')))
    C3.add_gate(Gate('F', AND, ('D', 'E')))
    C3.mark_as_output('F')

    manipulateC0 = copy.copy(C0)

    # this_connectors=outputs
    manipulateC0.connect_circuit(['C'], C1, ['A'], circuit_name='C1')
    assert manipulateC0.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', INPUT),
        'C': Gate('C', OR, ('A', 'B')),
        'C1@B': Gate('C1@B', INPUT),
        'C1@C': Gate('C1@C', AND, ('C', 'C1@B')),
    }
    assert manipulateC0.inputs == ['B', 'A', 'C1@B']

    # this_connectors=inputs
    manipulateC1 = copy.copy(C0)
    manipulateC1.connect_circuit(['A'], C1, ['B'], circuit_name='C1')
    assert manipulateC1.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', INPUT),
        'C': Gate('C', OR, ('A', 'B')),
        'C1@A': Gate('C1@A', INPUT),
        'C1@C': Gate('C1@C', AND, ('C1@A', 'A')),
    }
    assert manipulateC1.inputs == ['B', 'A', 'C1@A']

    # this_connectors=mix
    manipulateC2 = copy.copy(C2)
    manipulateC2.connect_circuit(['B', 'D', 'F'], C3, C3.inputs, circuit_name='C3')
    assert manipulateC2.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', INPUT),
        'C': Gate('C', INPUT),
        'D': Gate('D', OR, ('A', 'B')),
        'E': Gate('E', AND, ('C', 'D')),
        'F': Gate('F', AND, ('D', 'E')),
        'C3@D': Gate('C3@D', OR, ('B', 'D')),
        'C3@E': Gate('C3@E', AND, ('F', 'C3@D')),
        'C3@F': Gate('C3@F', AND, ('C3@D', 'C3@E')),
    }
    assert manipulateC2.inputs == ['C', 'B', 'A']

    with pytest.raises(CreateBlockError):
        manipulateC0.connect_circuit(
            ['C'], C1, ['A'], right_connect=True, circuit_name='C2'
        )

    # other_connerctors=outputs
    manipulateC3 = copy.copy(C0)
    manipulateC3.connect_circuit(
        ['A'], C1, ['C'], right_connect=True, circuit_name='C1'
    )
    assert manipulateC3.gates == {
        'A': Gate('A', AND, ('C1@A', 'C1@B')),
        'B': Gate('B', INPUT),
        'C': Gate('C', OR, ('A', 'B')),
        'C1@A': Gate('C1@A', INPUT),
        'C1@B': Gate('C1@B', INPUT),
    }
    assert manipulateC3.inputs == ['B', 'C1@B', 'C1@A']

    # other_connerctors=inputs
    manipulateC4 = copy.copy(C0)
    manipulateC4.connect_circuit(
        ['B'], C1, ['A'], right_connect=True, circuit_name='C1'
    )
    assert manipulateC4.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', INPUT),
        'C': Gate('C', OR, ('A', 'B')),
        'C1@B': Gate('C1@B', INPUT),
        'C1@C': Gate('C1@C', AND, ('B', 'C1@B')),
    }
    assert manipulateC4.inputs == ['B', 'A', 'C1@B']

    # other_connerctors=mix
    manipulateC5 = copy.copy(C2)
    manipulateC5.connect_circuit(
        ['A', 'B', 'C'], C3, ['B', 'D', 'F'], right_connect=True, circuit_name='C3'
    )
    assert manipulateC5.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', OR, ('C3@A', 'A')),
        'C': Gate('C', AND, ('B', 'C3@E')),
        'D': Gate('D', OR, ('A', 'B')),
        'E': Gate('E', AND, ('C', 'D')),
        'F': Gate('F', AND, ('D', 'E')),
        'C3@A': Gate('C3@A', INPUT),
        'C3@C': Gate('C3@C', INPUT),
        'C3@E': Gate('C3@E', AND, ('C3@C', 'B')),
    }
    assert manipulateC5.inputs == ['A', 'C3@C', 'C3@A']

    manipulateC6 = copy.copy(C0)
    manipulateC6.make_block_from_slice('inp', C0.inputs, C0.inputs)
    assert manipulateC6.get_block('inp').gates == []
    manipulateC6.connect_circuit(
        manipulateC6.get_block('inp').inputs, C1, C1.inputs, circuit_name='C1'
    )
    assert manipulateC6.gates == {
        'A': Gate('A', INPUT),
        'B': Gate('B', INPUT),
        'C': Gate('C', OR, ('A', 'B')),
        'C1@C': Gate('C1@C', AND, ('A', 'B')),
    }
    assert manipulateC6.inputs == ['B', 'A']


def test_block2():
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

    C.add_circuit(C0, circuit_name='C0')
    assert C.size == 3
    assert C.gates_number() == 1
    assert C.inputs == ['C0@B', 'C0@A']
    assert C.outputs == ['C0@C']
    assert C._gates.keys() == {'C0@A', 'C0@B', 'C0@C'}
    assert C.get_gate('C0@C').gate_type == OR
    assert C.get_gate('C0@C').operands == ('C0@A', 'C0@B')

    C.make_block_from_slice('backup_C0', C.inputs, C.outputs)
    BackUpC0 = C.get_block('backup_C0').into_circuit()
    assert BackUpC0.size == 3
    assert BackUpC0.gates_number() == 1
    assert BackUpC0.inputs == ['C0@B', 'C0@A']
    assert BackUpC0.outputs == ['C0@C']
    assert BackUpC0._gates.keys() == {'C0@A', 'C0@B', 'C0@C'}
    assert BackUpC0.get_gate('C0@C').gate_type == OR
    assert BackUpC0.get_gate('C0@C').operands == ('C0@A', 'C0@B')

    C.extend_circuit(C1, circuit_name='C1')
    assert C.size == 6
    assert C.gates_number() == 3
    assert C.inputs == ['C0@B', 'C0@A']
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

    C.make_block_from_slice('backup_C0_C1', C.inputs, C.outputs)
    with pytest.raises(CreateBlockError):
        C.make_block_from_slice('make_B1', C.inputs[1:], ['C1@C'])
    C.connect_circuit(C.outputs[1:], C2, C2.inputs[:1], circuit_name='C2')
    assert C.size == 8
    assert C.gates_number() == 4
    assert C.inputs == ['C0@B', 'C0@A', 'C2@B']
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
    C.make_block_from_slice('make_B1', C.inputs[:2], ['C1@C'])

    C2.connect_circuit(C2.outputs, C, ['C0@A'], circuit_name='C')
    assert C2.size == 10
    assert C2.gates_number() == 5
    assert C2.inputs == ['A', 'B', 'C@C2@B', 'C@C0@B']
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
        'C@C0',
        'C@backup_C0',
        'C@C1',
        'C@backup_C0_C1',
        'C@C2',
        'C@make_B1',
        'C',
    ]
    assert C2.get_block('C@C0').inputs == ['C', 'C@C0@B']
    assert C2.get_block('C@C0').gates == ['C@C0@C']
    assert C2.get_block('C@C0').outputs == ['C@C0@C']

    C3 = Circuit()
    C3.add_inputs(['A', 'B'])
    C3.add_gate(Gate('C', AND, ('A', 'B')))
    C3.mark_as_output('C')

    C3.connect_circuit(C3.outputs, C, ['C0@A'], circuit_name='')
    assert C3.size == 10
    assert C3.gates_number() == 5
    assert C3.inputs == ['A', 'B', 'C2@B', 'C0@B']
    assert C3.outputs == ['C1@C', 'C2@C']
    assert C3.input_size == 4
    assert C3.output_size == 2

    assert C3.get_gate('A').label == 'A'
    assert C3.get_gate('A').gate_type == INPUT
    assert C3.get_gate('A').operands == ()
    assert C3.get_gate_users('A') == ['C']

    assert C3.get_gate('B').label == 'B'
    assert C3.get_gate('B').gate_type == INPUT
    assert C3.get_gate('B').operands == ()
    assert C3.get_gate_users('B') == ['C']

    assert C3.get_gate('C').label == 'C'
    assert C3.get_gate('C').gate_type == AND
    assert C3.get_gate('C').operands == ('A', 'B')
    assert C3.get_gate_users('C') == ['C0@C']

    assert C3.get_gate('C0@B').label == 'C0@B'
    assert C3.get_gate('C0@B').gate_type == INPUT
    assert C3.get_gate('C0@B').operands == ()
    assert C3.get_gate_users('C0@B') == ['C0@C']

    assert C3.get_gate('C2@B').label == 'C2@B'
    assert C3.get_gate('C2@B').gate_type == INPUT
    assert C3.get_gate('C2@B').operands == ()
    assert C3.get_gate_users('C2@B') == ['C2@C']

    assert C3.get_gate('C0@C').label == 'C0@C'
    assert C3.get_gate('C0@C').gate_type == OR
    assert C3.get_gate('C0@C').operands == ('C', 'C0@B')
    assert C3.get_gate_users('C0@C') == ['C1@B', 'C1@C', 'C1@D']

    assert C3.get_gate('C1@B').label == 'C1@B'
    assert C3.get_gate('C1@B').gate_type == NOT
    assert C3.get_gate('C1@B').operands == ('C0@C',)
    assert C3.get_gate_users('C1@B') == ['C1@C', 'C1@D']

    assert C3.get_gate('C1@C').label == 'C1@C'
    assert C3.get_gate('C1@C').gate_type == AND
    assert C3.get_gate('C1@C').operands == ('C0@C', 'C1@B')
    assert C3.get_gate_users('C1@C') == []

    assert C3.get_gate('C1@D').label == 'C1@D'
    assert C3.get_gate('C1@D').gate_type == OR
    assert C3.get_gate('C1@D').operands == ('C0@C', 'C1@B')
    assert C3.get_gate_users('C1@D') == ['C2@C']

    assert C3.get_gate('C2@C').label == 'C2@C'
    assert C3.get_gate('C2@C').gate_type == AND
    assert C3.get_gate('C2@C').operands == ('C1@D', 'C2@B')
    assert C3.get_gate_users('C2@C') == []

    assert list(C3.blocks.keys()) == [
        'C0',
        'backup_C0',
        'C1',
        'backup_C0_C1',
        'C2',
        'make_B1',
    ]

    assert C3.get_block('C0').inputs == ['C', 'C0@B']
    assert C3.get_block('C0').gates == ['C0@C']
    assert C3.get_block('C0').outputs == ['C0@C']

    C3.delete_block('backup_C0_C1')
    assert list(C3.blocks.keys()) == [
        'C0',
        'backup_C0',
        'C1',
        'C2',
        'make_B1',
    ]

    C3.rename_gate('C0@C', 'my_favorite_gate')
    assert C3.size == 10
    assert C3.gates_number() == 5
    assert C3.get_gate('my_favorite_gate').label == 'my_favorite_gate'
    assert C3.get_gate('my_favorite_gate').gate_type == OR
    assert C3.get_gate('my_favorite_gate').operands == ('C', 'C0@B')
    assert C3.get_gate_users('my_favorite_gate') == ['C1@B', 'C1@C', 'C1@D']

    assert C3.get_gate('C2@B').label == 'C2@B'
    assert C3.get_gate('C2@B').gate_type == INPUT
    assert C3.get_gate('C2@B').operands == ()
    assert C3.get_gate_users('C2@B') == ['C2@C']

    assert C3.get_gate('C1@B').label == 'C1@B'
    assert C3.get_gate('C1@B').gate_type == NOT
    assert C3.get_gate('C1@B').operands == ('my_favorite_gate',)
    assert C3.get_gate_users('C1@B') == ['C1@C', 'C1@D']

    assert C3.get_block('C0').inputs == ['C', 'C0@B']
    assert C3.get_block('C0').gates == ['my_favorite_gate']
    assert C3.get_block('C0').outputs == ['my_favorite_gate']


def test_block3():
    C0 = Circuit()
    C0.add_gate(Gate('x1', INPUT))
    C0.add_gate(Gate('x2', INPUT))
    C0.add_gate(Gate('x3', OR, ('x1', 'x2')))
    C0.mark_as_output('x3')

    C1 = Circuit()
    C1.add_gate(Gate('y1', INPUT))
    C1.add_gate(Gate('y2', INPUT))
    C1.add_gate(Gate('y3', AND, ('y1', 'y2')))
    C1.mark_as_output('y3')

    manipulateC0 = copy.copy(C0)

    manipulateC0.connect_circuit(
        ['x3'], C1, ['y1'], circuit_name='C1', add_prefix=False
    )
    assert manipulateC0.gates == {
        'x1': Gate('x1', INPUT),
        'x2': Gate('x2', INPUT),
        'x3': Gate('x3', OR, ('x1', 'x2')),
        'y2': Gate('y2', INPUT),
        'y3': Gate('y3', AND, ('x3', 'y2')),
    }

    manipulateC0.make_block('new_block', ['y3'], ['y3'])
    assert manipulateC0.get_block('new_block').inputs == ['x3', 'y2']

    manipulateC0.remove_block('C1')
    assert manipulateC0.gates == {
        'x1': Gate('x1', INPUT),
        'x2': Gate('x2', INPUT),
        'y2': Gate('y2', INPUT),
        'x3': Gate('x3', OR, ('x1', 'x2')),
    }


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
    assert instance.evaluate([Undefined, True]) == [True, Undefined, True]
    assert instance.evaluate([Undefined, Undefined]) == [
        Undefined,
        Undefined,
        Undefined,
    ]

    with pytest.raises(GateNotInputError):
        instance.replace_inputs(['D'], ['C'])

    assert instance.inputs == ['A', 'B']
    instance.replace_inputs([], ['B'])
    assert instance.inputs == ['A']

    assert instance.evaluate([False]) == [False, False, False]
    assert instance.evaluate([True]) == [True, True, False]
    assert instance.evaluate([Undefined]) == [Undefined, Undefined, False]

    instance.set_outputs(['E'])
    assert instance.evaluate([False]) == [False]
    assert instance.evaluate([True]) == [True]
    assert instance.evaluate([Undefined]) == [Undefined]


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
    assert instance.gates_number() == 1
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