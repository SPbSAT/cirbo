from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.gate import Gate, OR
from cirbo.synthesis.generation import generate_pairwise_xor
from cirbo.synthesis.generation.arithmetics import generate_sum_n_bits

aig = generate_sum_n_bits(3, basis='AIG')
xaig = generate_sum_n_bits(3, basis='XAIG')

mtr = Circuit().add_circuit(aig, name='aig')
mtr.connect_inputs(xaig, name='xaig')
mtr.extend_circuit(
    generate_pairwise_xor(aig.output_size),
    name='pairwise_xor',
)  

outs = mtr.get_block('pairwise_xor').outputs      
mtr.emplace_gate('or', OR, tuple(outs))
mtr.set_outputs(['or'])

mtr.view_graph(autorename_labels=True)
