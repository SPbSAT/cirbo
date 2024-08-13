from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
from boolean_circuit_tool.minimization.simplification import cleanup


ckt = Circuit(n=7)
*_, b2 = add_sum_n_bits(ckt, ckt.inputs)
ckt.mark_as_output(b2)
cleanup(ckt)