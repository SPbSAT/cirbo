from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, OR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits


ckt = Circuit.bare_circuit(6, prefix='x')
b0, b1, b2 = add_sum_n_bits(ckt, ckt.inputs)
ckt.add_gate(Gate('a0', AND, (b0, b1)))
ckt.add_gate(Gate('a1', OR, ('a0', b2)))
ckt.mark_as_output('a1')
ckt.into_graphviz_digraph().view()