from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.minimization.simplification import cleanup
from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits


ckt = Circuit.bare_circuit(7)
*_, b2 = add_sum_n_bits(ckt, ckt.inputs)
ckt.mark_as_output(b2)
print(ckt.size)
ckt = cleanup(ckt)
print(ckt.size)