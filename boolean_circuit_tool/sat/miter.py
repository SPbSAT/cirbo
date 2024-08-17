from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.sat.exceptions import MiterDifferentShapesError

__all__ = [
    'build_miter',
]

FIRST_CIRCUIT_NAME = 'circuit1'
SECOND_CIRCUIT_NAME = 'circuit2'
PAIRWISE_XOR_NAME = 'pairwise_xor'
OR_NAME = 'big_or'


def build_miter(
    left: Circuit,
    right: Circuit,
    *,
    left_name: gate.Label = FIRST_CIRCUIT_NAME,
    right_name: gate.Label = SECOND_CIRCUIT_NAME
) -> Circuit:
    """
    Given two circuit, returns a miter circuit (that checks whether the two circuits are
    equivalent).

    :param left: first circuit
    :param right: second circuit
    :param left_name: name for the block that is added for the first circuit
    :param right_name: name for the block that is added for the second circuit
    :return: a miter circuit of given circuits

    """
    from boolean_circuit_tool.synthesis.generation import generate_pairwise_xor

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
        name=PAIRWISE_XOR_NAME,
    )
    miter.emplace_gate(
        OR_NAME, gate.OR, tuple(miter.get_block(PAIRWISE_XOR_NAME).outputs)
    )
    miter.set_outputs([OR_NAME])

    return miter
