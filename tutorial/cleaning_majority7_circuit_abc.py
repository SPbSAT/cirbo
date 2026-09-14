from cirbo.core.circuit import Circuit
from cirbo.integrations.abc import abc_transform
from cirbo.synthesis.generation.arithmetics import add_sum_n_bits

ckt = Circuit.bare_circuit(input_size=7)
*_, lst = add_sum_n_bits(ckt, ckt.inputs, basis='AIG')
ckt.mark_as_output(lst)
ckt = abc_transform(ckt, 'strash; dc2')
