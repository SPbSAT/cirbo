from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits
from boolean_circuit_tool.core.circuit import Circuit
from extensions.abc_wrapper.src.abc import abc_transform

ckt = Circuit.bare_circuit(input_size=7)
*_, lst = add_sum_n_bits(ckt, ckt.inputs, basis='AIG')
ckt.mark_as_output(lst)
ckt = abc_transform(ckt, 'strash; dc2')
