from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.synthesis.exceptions_gen import (
    PairwiseIfThenElseDifferentShapesError,
    PairwiseXorDifferentShapesError,
)

__all__ = [
    'generate_plus_one',
    'generate_if_then_else',
    'generate_pairwise_if_then_else',
    'generate_pairwise_xor',
    'generate_inputs_with_labels',
    'generate_inputs',
]


def generate_plus_one(inp_len: int, out_len: int) -> Circuit:
    x_labels = _generate_labels('x', inp_len)
    z_labels = _generate_labels('z', out_len)
    circuit = Circuit()
    circuit.add_inputs(x_labels)

    return add_plus_one(circuit, z_labels, x_labels)


def generate_if_then_else() -> Circuit:
    circuit = Circuit()
    circuit.add_inputs(['if', 'then', 'else'])

    return add_if_then_else(circuit, 'if_then_else', 'if', 'then', 'else')


def generate_pairwise_if_then_else(n: int) -> Circuit:
    if_labels = _generate_labels('if', n)
    then_labels = _generate_labels('then', n)
    else_labels = _generate_labels('else', n)
    if_then_else_labels = _generate_labels('if_then_else', n)

    circuit = Circuit()
    circuit.add_inputs(if_labels)
    circuit.add_inputs(then_labels)
    circuit.add_inputs(else_labels)

    return add_pairwise_if_then_else(
        circuit, if_then_else_labels, if_labels, then_labels, else_labels
    )


def generate_pairwise_xor(n: int) -> Circuit:
    x_labels = _generate_labels('x', n)
    y_labels = _generate_labels('y', n)
    xor_labels = _generate_labels('xor', n)

    circuit = Circuit()
    circuit.add_inputs(x_labels)
    circuit.add_inputs(y_labels)

    return add_pairwise_xor(circuit, xor_labels, x_labels, y_labels)


def generate_inputs_with_labels(labels: list[gate.Label]) -> Circuit:
    circuit = Circuit()
    circuit.add_inputs(labels)
    circuit.set_outputs(labels)
    return circuit


def generate_inputs(n: int) -> Circuit:
    return generate_inputs_with_labels(_generate_labels('x', n))


def add_plus_one(
    circuit: Circuit, result_labels: list[gate.Label], input_labels: list[gate.Label]
) -> Circuit:
    inp_len = len(input_labels)
    out_len = len(result_labels)

    circuit.add_gate(Gate('carry_0', gate.IFF, (input_labels[0],)))
    circuit.add_gate(
        Gate(result_labels[0], gate.NOT, (input_labels[0],))
    ).mark_as_output(result_labels[0])

    for i in range(1, out_len):
        if i < inp_len:
            if i < out_len - 1:
                circuit.add_gate(
                    Gate(
                        'carry_' + str(i),
                        gate.AND,
                        ('x_' + str(i), 'carry_' + str(i - 1)),
                    )
                )
            circuit.add_gate(
                Gate('z_' + str(i), gate.XOR, ('x_' + str(i), 'carry_' + str(i - 1)))
            )
        elif i == inp_len:
            circuit.add_gate(Gate('z_' + str(i), gate.IFF, ('carry_' + str(i - 1),)))
        else:
            circuit.add_gate(Gate('z_' + str(i), gate.ALWAYS_FALSE, tuple()))
        circuit.mark_as_output('z_' + str(i))

    return circuit.order_outputs(['z_' + str(i) for i in range(out_len)])


def add_if_then_else(
    circuit: Circuit,
    result_label: gate.Label,
    if_label: gate.Label,
    then_label: gate.Label,
    else_label: gate.Label,
) -> Circuit:
    (
        circuit.add_gate(Gate('tmp1' + result_label, gate.AND, (if_label, then_label)))
        .add_gate(Gate('tmp2' + result_label, gate.NOT, (if_label,)))
        .add_gate(
            Gate('tmp3' + result_label, gate.AND, ('tmp2' + result_label, else_label))
        )
        .add_gate(
            Gate(result_label, gate.OR, ('tmp1' + result_label, 'tmp3' + result_label))
        )
        .mark_as_output(result_label)
    )
    return circuit


def add_pairwise_if_then_else(
    circuit: Circuit,
    result_labels: list[gate.Label],
    if_inputs: list[gate.Label],
    then_inputs: list[gate.Label],
    else_inputs: list[gate.Label],
) -> Circuit:
    if len(if_inputs) != len(then_inputs) or len(then_inputs) != len(else_inputs):
        raise PairwiseIfThenElseDifferentShapesError()
    n = len(if_inputs)
    for i in range(n):
        add_if_then_else(
            circuit, result_labels[i], if_inputs[i], then_inputs[i], else_inputs[i]
        )

    return circuit


def add_pairwise_xor(
    circuit: Circuit,
    result_labels: list[gate.Label],
    x_labels: list[gate.Label],
    y_labels: list[gate.Label],
) -> Circuit:
    if len(x_labels) != len(y_labels):
        raise PairwiseXorDifferentShapesError()
    n = len(x_labels)
    for i in range(n):
        circuit.add_gate(Gate(result_labels[i], gate.XOR, (x_labels[i], y_labels[i])))
        circuit.mark_as_output(result_labels[i])
    return circuit


def _generate_labels(prefix: str, n: int) -> list[str]:
    return [prefix + '_' + str(i) for i in range(n)]
