from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, OR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits


ckt = Circuit()
ckt.add_inputs(['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
b0, b1, b2 = add_sum_n_bits(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
ckt.add_gate(Gate('a0', AND, (b0, b1)))
ckt.add_gate(Gate('a1', OR, ('a0', b2)))
ckt.mark_as_output('a1')
