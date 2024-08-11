from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.sat.exceptions import MiterDifferentShapesError
from boolean_circuit_tool.synthesis.generation import generate_pairwise_xor


__all__ = [
    'build_miter',
]


def build_miter(
    left: Circuit,
    right: Circuit,
    *,
    left_name: gate.Label = 'circuit1',
    right_name: gate.Label = 'circuit2'
) -> Circuit:
    if (left.input_size != right.input_size) or (left.output_size != right.output_size):
        raise MiterDifferentShapesError()

    miter = Circuit().add_circuit(left, name=left_name)
    miter.connect_circuit(
        right,
        miter.get_block(left_name).inputs,
        right.inputs,
        name=right_name,
    )
    pairwise_xor = generate_pairwise_xor(left.output_size)
    miter.connect_circuit(
        pairwise_xor,
        miter.get_block(left_name).outputs + miter.get_block(right_name).outputs,
        pairwise_xor.inputs,
        name='pairwise_xor',
    )
    miter.emplace_gate(
        'big_or', gate.OR, tuple(miter.get_block('pairwise_xor').outputs)
    )
    miter.set_outputs(['big_or'])

    return miter
