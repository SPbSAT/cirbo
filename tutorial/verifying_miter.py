from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.sat import is_circuit_satisfiable
from boolean_circuit_tool.synthesis.generation import generate_pairwise_xor
from boolean_circuit_tool.synthesis.generation.arithmetics import generate_sum_n_bits


sum3_aig = generate_sum_n_bits(n=3, basis='AIG')
sum3_xaig = generate_sum_n_bits(n=3, basis='ALL')

miter = Circuit().add_circuit(sum3_aig, name='sum3_aig')
miter.extend_circuit(sum3_xaig, this_connectors=miter.inputs, name='sum3_xaig')\
    .extend_circuit(
        generate_pairwise_xor(sum3_aig.output_size),
        this_connectors=(miter.get_block('sum3_aig').outputs + miter.get_block('sum3_xaig').outputs),
        name='pairwise_xor')\
    .emplace_gate('or', gate.OR, tuple(miter.get_block('pairwise_xor').outputs))\
    .set_outputs(['or'])

assert is_circuit_satisfiable(miter).answer == False
