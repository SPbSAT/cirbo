from boolean_circuit_tool.core.circuit import Circuit, OR
from boolean_circuit_tool.synthesis.generation import generate_pairwise_xor


def build_miter(circuit1: Circuit, circuit2: Circuit) -> Circuit:
    assert (circuit1.input_size == circuit2.input_size)
    assert (circuit1.output_size == circuit2.output_size)

    miter = Circuit().add_circuit(circuit1, circuit_name='circuit1')
    miter.connect_circuit(miter.get_block('circuit1').inputs, circuit2, circuit2.inputs, circuit_name='circuit2')
    pairwise_xor = generate_pairwise_xor(circuit1.output_size)
    miter.connect_circuit(miter.get_block('circuit1').outputs+miter.get_block('circuit2').outputs, pairwise_xor,
                          pairwise_xor.inputs, circuit_name='pairwise_xor')
    miter.emplace_gate('big_or', OR, tuple(miter.get_block('pairwise_xor').outputs))
    miter.set_outputs(['big_or'])

    return miter
