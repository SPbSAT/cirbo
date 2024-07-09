import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import AND, INPUT, NOT, OR


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

    assert instance.gates_number == 5
    assert instance._input_gates == ['A', 'D', 'E']
    assert instance._output_gates == ['C']

    assert instance._gates.keys() == {'A', 'D', 'B', 'C', 'E'}
    assert instance._gates['A'].label == 'A'
    assert instance._gates['A'].gate_type == INPUT
    assert tuple(instance._gates['A'].operands) == ()

    assert instance._gates['D'].label == 'D'
    assert instance._gates['D'].gate_type == INPUT
    assert tuple(instance._gates['D'].operands) == ()

    assert instance._gates['E'].label == 'E'
    assert instance._gates['E'].gate_type == INPUT
    assert tuple(instance._gates['E'].operands) == ()

    assert instance._gates['B'].label == 'B'
    assert instance._gates['B'].gate_type == NOT
    assert tuple(instance._gates['B'].operands) == ('A',)

    assert instance._gates['C'].label == 'C'
    assert instance._gates['C'].gate_type == AND
    assert tuple(instance._gates['C'].operands) == ('A', 'B')


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

    assert instance.gates_number == 5
    assert instance._input_gates == ['AAAAA', 'DDDD', 'E']
    assert instance._output_gates == ['C']

    assert instance._gates.keys() == {'AAAAA', 'DDDD', 'B', 'C', 'E'}

    assert instance._gates['AAAAA'].label == 'AAAAA'
    assert instance._gates['AAAAA'].gate_type == INPUT
    assert tuple(instance._gates['AAAAA'].operands) == ()

    assert instance._gates['DDDD'].label == 'DDDD'
    assert instance._gates['DDDD'].gate_type == INPUT
    assert tuple(instance._gates['DDDD'].operands) == ()

    assert instance._gates['E'].label == 'E'
    assert instance._gates['E'].gate_type == INPUT
    assert tuple(instance._gates['E'].operands) == ()

    assert instance._gates['B'].label == 'B'
    assert instance._gates['B'].gate_type == NOT
    assert tuple(instance._gates['B'].operands) == ('AAAAA',)

    assert instance._gates['C'].label == 'C'
    assert instance._gates['C'].gate_type == AND
    assert tuple(instance._gates['C'].operands) == ('AAAAA', 'B')


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

    assert instance.gates_number == 3
    assert instance._input_gates == ['A']
    assert instance._output_gates == ['B']

    assert instance._gates.keys() == {'A', 'B', 'D'}
    assert instance._gates['A'].label == 'A'
    assert instance._gates['A'].gate_type == INPUT
    assert tuple(instance._gates['A'].operands) == ()

    assert instance._gates['B'].label == 'B'
    assert instance._gates['B'].gate_type == OR
    assert tuple(instance._gates['B'].operands) == ('A', 'D')

    assert instance._gates['D'].label == 'D'
    assert instance._gates['D'].gate_type == NOT
    assert tuple(instance._gates['D'].operands) == ('A',)


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

    assert instance.gates_number == 5
    assert instance._input_gates == ['A', 'D', 'E']
    assert instance._output_gates == ['C', 'A']

    instance.sort_inputs(['E', 'A'])
    assert instance._input_gates == ['E', 'A', 'D']

    instance.sort_outputs(['A', 'C'])
    assert instance._output_gates == ['A', 'C']
