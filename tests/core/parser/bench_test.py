import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import (
    AND,
    INPUT,
    NOT,
    OR,
)


def test_trivial_instance():

    file_input = """
# Comment Line\n
#\n
\n
INPUT(A)\n
INPUT(D)\n
OUTPUT(C)\n
B = NOT(A)\n
C = AND(A, B)\n
INPUT(E)\n
"""
    instance = Circuit().from_bench(file_input.split("\n"))

    assert instance.elements_number == 5
    assert instance._inputs == ['A', 'D', 'E']
    assert instance._outputs == ['C']

    assert instance._elements.keys() == {'A', 'D', 'B', 'C', 'E'}
    assert instance._elements['A'].label == 'A'
    assert instance._elements['A'].gate_type == INPUT
    assert instance._elements['A'].operands == ()

    assert instance._elements['D'].label == 'D'
    assert instance._elements['D'].gate_type == INPUT
    assert instance._elements['D'].operands == ()

    assert instance._elements['E'].label == 'E'
    assert instance._elements['E'].gate_type == INPUT
    assert instance._elements['E'].operands == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert instance._elements['B'].operands == ('A',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert instance._elements['C'].operands == ('A', 'B')


def test_spaces():

    file_input = """
INPUT(    AAAAA)\n
INPUT(DDDD    )\n
OUTPUT(  C  )\n
B =     NOT(AAAAA)    \n
C     = AND(AAAAA,     B)\n
INPUT(E   )\n
"""
    instance = Circuit().from_bench(file_input.split("\n"))

    assert instance.elements_number == 5
    assert instance._inputs == ['AAAAA', 'DDDD', 'E']
    assert instance._outputs == ['C']

    assert instance._elements.keys() == {'AAAAA', 'DDDD', 'B', 'C', 'E'}

    assert instance._elements['AAAAA'].label == 'AAAAA'
    assert instance._elements['AAAAA'].gate_type == INPUT
    assert instance._elements['AAAAA'].operands == ()

    assert instance._elements['DDDD'].label == 'DDDD'
    assert instance._elements['DDDD'].gate_type == INPUT
    assert instance._elements['DDDD'].operands == ()

    assert instance._elements['E'].label == 'E'
    assert instance._elements['E'].gate_type == INPUT
    assert instance._elements['E'].operands == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == NOT
    assert instance._elements['B'].operands == ('AAAAA',)

    assert instance._elements['C'].label == 'C'
    assert instance._elements['C'].gate_type == AND
    assert instance._elements['C'].operands == ('AAAAA', 'B')


def test_not_init_operands():

    file_input = """
INPUT(A)\n
OUTPUT(B)\n
B = OR(A, D)\n
"""
    with pytest.raises(CircuitValidationError):
        Circuit().from_bench(file_input.split("\n"))


def test_init_operands_after_using():

    file_input = """
INPUT(A)\n
OUTPUT(B)\n
B = OR(A, D)\n
D = NOT(A)
"""
    instance = Circuit().from_bench(file_input.split("\n"))

    assert instance.elements_number == 3
    assert instance._inputs == ['A']
    assert instance._outputs == ['B']

    assert instance._elements.keys() == {'A', 'B', 'D'}
    assert instance._elements['A'].label == 'A'
    assert instance._elements['A'].gate_type == INPUT
    assert instance._elements['A'].operands == ()

    assert instance._elements['B'].label == 'B'
    assert instance._elements['B'].gate_type == OR
    assert instance._elements['B'].operands == ('A', 'D')

    assert instance._elements['D'].label == 'D'
    assert instance._elements['D'].gate_type == NOT
    assert instance._elements['D'].operands == ('A',)


def test_sorting():

    file_input = """
# Comment Line\n
#\n
\n
INPUT(A)\n
INPUT(D)\n
OUTPUT(C)\n
B = NOT(A)\n
C = AND(A, B)\n
INPUT(E)\n
OUTPUT(A)\n
"""
    instance = Circuit().from_bench(file_input.split("\n"))

    assert instance.elements_number == 5
    assert instance._inputs == ['A', 'D', 'E']
    assert instance._outputs == ['C', 'A']

    instance.sort_inputs(['E', 'A'])
    assert instance._inputs == ['E', 'A', 'D']

    instance.sort_outputs(['A', 'C'])
    assert instance._outputs == ['A', 'C']
