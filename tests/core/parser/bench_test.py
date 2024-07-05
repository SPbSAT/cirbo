import pytest

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import CircuitValidationError
from boolean_circuit_tool.core.circuit.gate import GateType


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
    assert instance.input_gates == {'A', 'D', 'E'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'A', 'D', 'B', 'C', 'E'}
    assert instance.gates['A'].label == 'A'
    assert instance.gates['A'].gate_type == GateType.INPUT
    assert tuple(instance.gates['A'].operands) == ()

    assert instance.gates['D'].label == 'D'
    assert instance.gates['D'].gate_type == GateType.INPUT
    assert tuple(instance.gates['D'].operands) == ()

    assert instance.gates['E'].label == 'E'
    assert instance.gates['E'].gate_type == GateType.INPUT
    assert tuple(instance.gates['E'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('A',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('A', 'B')


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
    assert instance.input_gates == {'AAAAA', 'DDDD', 'E'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'AAAAA', 'DDDD', 'B', 'C', 'E'}

    assert instance.gates['AAAAA'].label == 'AAAAA'
    assert instance.gates['AAAAA'].gate_type == GateType.INPUT
    assert tuple(instance.gates['AAAAA'].operands) == ()

    assert instance.gates['DDDD'].label == 'DDDD'
    assert instance.gates['DDDD'].gate_type == GateType.INPUT
    assert tuple(instance.gates['DDDD'].operands) == ()

    assert instance.gates['E'].label == 'E'
    assert instance.gates['E'].gate_type == GateType.INPUT
    assert tuple(instance.gates['E'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('AAAAA',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.AND
    assert tuple(instance.gates['C'].operands) == ('AAAAA', 'B')


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
    assert instance.input_gates == {'A'}
    assert instance.output_gates == {'B'}

    assert instance.gates.keys() == {'A', 'B', 'D'}
    assert instance.gates['A'].label == 'A'
    assert instance.gates['A'].gate_type == GateType.INPUT
    assert tuple(instance.gates['A'].operands) == ()

    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.OR
    assert tuple(instance.gates['B'].operands) == ('A', 'D')

    assert instance.gates['D'].label == 'D'
    assert instance.gates['D'].gate_type == GateType.NOT
    assert tuple(instance.gates['D'].operands) == ('A',)
