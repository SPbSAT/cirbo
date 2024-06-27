from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.exceptions import CircuitValidationError
from boolean_circuit_tool.core.gate import GateType


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

    assert instance.gates.keys() == {'B', 'C'}
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
C     = MUX(AAAAA,     B, C)\n
INPUT(E   )\n
"""
    instance = Circuit().from_bench(file_input.split("\n"))

    assert instance.gates_number == 5
    assert instance.input_gates == {'AAAAA', 'DDDD', 'E'}
    assert instance.output_gates == {'C'}

    assert instance.gates.keys() == {'B', 'C'}
    assert instance.gates['B'].label == 'B'
    assert instance.gates['B'].gate_type == GateType.NOT
    assert tuple(instance.gates['B'].operands) == ('AAAAA',)

    assert instance.gates['C'].label == 'C'
    assert instance.gates['C'].gate_type == GateType.MUX
    assert tuple(instance.gates['C'].operands) == ('AAAAA', 'B', 'C')


def test_not_init_operands():

    file_input = """
INPUT(A)\n
OUTPUT(C)\n
B = OR(A, D)\n
"""
    try:
        instance = Circuit().from_bench(file_input.split("\n"))
        assert False
    except CircuitValidationError:
        assert True
