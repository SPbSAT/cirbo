from boolean_circuit_tool.core import Circuit
from boolean_circuit_tool.minimization import cleanup
from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits


ckt = Circuit.bare_circuit(input_size=7)
*_, b2 = add_sum_n_bits(ckt, ckt.inputs)
ckt.mark_as_output(b2)
print(ckt.gates_number())
ckt = cleanup(ckt)
print(ckt.gates_number())
