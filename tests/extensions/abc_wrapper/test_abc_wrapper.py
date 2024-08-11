import io

import pytest

# Package can be compiled without ABC extension when
# environment variable DISABLE_ABC_CEXT=1 is set.
#
try:
    from abc_wrapper import run_abc_commands
except ImportError:
    pass

from boolean_circuit_tool.core.circuit import AND, Circuit, Gate, INPUT, NOT, OR
from boolean_circuit_tool.core.parser.bench import BenchToCircuit

ckt1 = Circuit()
ckt1.add_gate(Gate('x', INPUT))
ckt1.add_gate(Gate('y', INPUT))
ckt1.add_gate(Gate('z', INPUT))
ckt1.add_gate(Gate('nx', NOT, ('x',)))
ckt1.add_gate(Gate('ny', NOT, ('y',)))
ckt1.add_gate(Gate('and1', AND, ('nx', 'ny')))
ckt1.add_gate(Gate('or1', OR, ('and1', 'y')))
ckt1.add_gate(Gate('and2', AND, ('nx', 'z')))
ckt1.add_gate(Gate('or2', OR, ('or1', 'and2')))
ckt1.mark_as_output('or2')

ckt2 = Circuit()
ckt2.add_gate(Gate('x', INPUT))
ckt2.add_gate(Gate('y', INPUT))
ckt2.add_gate(Gate('z', INPUT))
ckt2.add_gate(Gate('nx', NOT, ('x',)))
ckt2.add_gate(Gate('ny', NOT, ('y',)))
ckt2.add_gate(Gate('nz', NOT, ('z',)))

ckt2.add_gate(Gate('g1', AND, ('nx', 'y')))
ckt2.add_gate(Gate('g2', AND, ('g1', 'z')))

ckt2.add_gate(Gate('g3', AND, ('x', 'ny')))
ckt2.add_gate(Gate('g4', AND, ('g3', 'z')))

ckt2.add_gate(Gate('g5', AND, ('x', 'y')))
ckt2.add_gate(Gate('g6', AND, ('g5', 'nz')))

ckt2.add_gate(Gate('g7', AND, ('x', 'y')))
ckt2.add_gate(Gate('g8', AND, ('g7', 'z')))

ckt2.add_gate(Gate('g9', OR, ('g2', 'g4')))
ckt2.add_gate(Gate('g10', OR, ('g9', 'g6')))
ckt2.add_gate(Gate('g11', OR, ('g10', 'g8')))
ckt2.mark_as_output('g11')


@pytest.mark.ABC
def test_run_abc_commands():
    assert callable(run_abc_commands)


@pytest.mark.ABC
@pytest.mark.parametrize("circuit, expected_size", [(ckt1, 1), (ckt2, 4)])
def test_abc_dc2(circuit: Circuit, expected_size: int):
    command = "strash; dc2"
    simp_ckt_str = run_abc_commands(circuit.format_circuit(), command)
    _parser = BenchToCircuit()
    with io.StringIO(simp_ckt_str) as file:
        simp_ckt = _parser.convert_to_circuit(file)
    assert simp_ckt.get_truth_table() == circuit.get_truth_table()
    assert simp_ckt.gates_number() == expected_size


@pytest.mark.ABC
@pytest.mark.parametrize("circuit, expected_size", [(ckt1, 2), (ckt2, 10)])
def test_abc_fraig(circuit: Circuit, expected_size: int):
    command = "strash; fraig"
    simp_ckt_str = run_abc_commands(circuit.format_circuit(), command)
    _parser = BenchToCircuit()
    with io.StringIO(simp_ckt_str) as file:
        simp_ckt = _parser.convert_to_circuit(file)
    assert simp_ckt.get_truth_table() == circuit.get_truth_table()
    assert simp_ckt.gates_number() == expected_size


@pytest.mark.ABC
@pytest.mark.parametrize("circuit, expected_size", [(ckt1, 4), (ckt2, 6)])
def test_abc_rewrite(circuit: Circuit, expected_size: int):
    command = "strash; rewrite"
    simp_ckt_str = run_abc_commands(circuit.format_circuit(), command)
    _parser = BenchToCircuit()
    with io.StringIO(simp_ckt_str) as file:
        simp_ckt = _parser.convert_to_circuit(file)
    assert simp_ckt.get_truth_table() == circuit.get_truth_table()
    assert simp_ckt.gates_number() == expected_size


@pytest.mark.ABC
@pytest.mark.parametrize("circuit, expected_size", [(ckt1, 1), (ckt2, 4)])
def test_abc_simplify(circuit: Circuit, expected_size: int):
    command = "strash; dc2; drw; rewrite; refactor; resub"
    simp_ckt_str = run_abc_commands(circuit.format_circuit(), command)
    _parser = BenchToCircuit()
    with io.StringIO(simp_ckt_str) as file:
        simp_ckt = _parser.convert_to_circuit(file)
    assert simp_ckt.get_truth_table() == circuit.get_truth_table()
    assert simp_ckt.gates_number() == expected_size
