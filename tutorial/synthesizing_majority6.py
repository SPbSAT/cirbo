from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, OR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits


ckt = Circuit.bare_circuit(input_size=6)
b0, b1, b2 = add_sum_n_bits(ckt, ckt.inputs)
ckt.add_gate(Gate('a0', AND, (b0, b1)))
ckt.add_gate(Gate('a1', OR, ('a0', b2)))
ckt.mark_as_output('a1')
ckt.view_graph()
