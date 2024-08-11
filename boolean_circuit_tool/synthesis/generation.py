import uuid

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
    'add_plus_one',
    'add_if_then_else',
    'add_pairwise_if_then_else',
    'add_pairwise_xor',
]


def generate_plus_one(inp_len: int, out_len: int) -> Circuit:
    x_labels = _generate_labels('x', inp_len)
    z_labels = _generate_labels('z', out_len)
    circuit = Circuit()
    circuit.add_inputs(x_labels)

    add_plus_one(circuit, x_labels, result_labels=z_labels, add_outputs=True)
    return circuit


def generate_if_then_else() -> Circuit:
    circuit = Circuit()
    circuit.add_inputs(['if', 'then', 'else'])

    add_if_then_else(
        circuit, 'if', 'then', 'else', result_label='if_then_else', add_outputs=True
    )
    return circuit


def generate_pairwise_if_then_else(n: int) -> Circuit:
    if_labels = _generate_labels('if', n)
    then_labels = _generate_labels('then', n)
    else_labels = _generate_labels('else', n)
    if_then_else_labels = _generate_labels('if_then_else', n)

    circuit = Circuit()
    circuit.add_inputs(if_labels)
    circuit.add_inputs(then_labels)
    circuit.add_inputs(else_labels)

    add_pairwise_if_then_else(
        circuit,
        if_labels,
        then_labels,
        else_labels,
        result_labels=if_then_else_labels,
        add_outputs=True,
    )
    return circuit


def generate_pairwise_xor(n: int) -> Circuit:
    x_labels = _generate_labels('x', n)
    y_labels = _generate_labels('y', n)
    xor_labels = _generate_labels('xor', n)

    circuit = Circuit()
    circuit.add_inputs(x_labels)
    circuit.add_inputs(y_labels)

    add_pairwise_xor(
        circuit, x_labels, y_labels, result_labels=xor_labels, add_outputs=True
    )
    return circuit


def generate_inputs_with_labels(labels: list[gate.Label]) -> Circuit:
    circuit = Circuit()
    circuit.add_inputs(labels)
    circuit.set_outputs(labels)
    return circuit


def generate_inputs(n: int) -> Circuit:
    return generate_inputs_with_labels(_generate_labels('x', n))


def add_plus_one(
    circuit: Circuit,
    input_labels: list[gate.Label],
    *,
    result_labels: list[gate.Label] = None,
    add_outputs=False
) -> list[gate.Label]:
    inp_len = len(input_labels)

    if result_labels is None:
        result_labels = []
        for i in range(inp_len + 1):
            result_labels.append(_get_new_label(circuit))

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
                        (input_labels[i], 'carry_' + str(i - 1)),
                    )
                )
            circuit.add_gate(
                Gate(
                    result_labels[i], gate.XOR, (input_labels[i], 'carry_' + str(i - 1))
                )
            )
        elif i == inp_len:
            circuit.add_gate(Gate(result_labels[i], gate.IFF, ('carry_' + str(i - 1),)))
        else:
            circuit.add_gate(Gate(result_labels[i], gate.ALWAYS_FALSE, tuple()))
        if add_outputs:
            circuit.mark_as_output(result_labels[i])

    return result_labels


def add_if_then_else(
    circuit: Circuit,
    if_label: gate.Label,
    then_label: gate.Label,
    else_label: gate.Label,
    *,
    result_label: gate.Label = None,
    add_outputs=False
) -> gate.Label:
    if result_label is None:
        result_label = _get_new_label(circuit)

    circuit.add_gate(Gate('tmp1' + result_label, gate.AND, (if_label, then_label)))
    circuit.add_gate(Gate('tmp2' + result_label, gate.NOT, (if_label,)))
    circuit.add_gate(
        Gate('tmp3' + result_label, gate.AND, ('tmp2' + result_label, else_label))
    )
    circuit.add_gate(
        Gate(result_label, gate.OR, ('tmp1' + result_label, 'tmp3' + result_label))
    )
    if add_outputs:
        circuit.mark_as_output(result_label)

    return result_label


def add_pairwise_if_then_else(
    circuit: Circuit,
    if_inputs: list[gate.Label],
    then_inputs: list[gate.Label],
    else_inputs: list[gate.Label],
    *,
    result_labels: list[gate.Label] = None,
    add_outputs=False
) -> list[gate.Label]:
    if len(if_inputs) != len(then_inputs) or len(then_inputs) != len(else_inputs):
        raise PairwiseIfThenElseDifferentShapesError()

    n = len(if_inputs)
    if result_labels is None:
        result_labels = []
        for i in range(n):
            result_labels.append(_get_new_label(circuit))

    if len(result_labels) != n:
        raise PairwiseIfThenElseDifferentShapesError()

    for i in range(n):
        add_if_then_else(
            circuit,
            if_inputs[i],
            then_inputs[i],
            else_inputs[i],
            result_label=result_labels[i],
            add_outputs=add_outputs,
        )

    return result_labels


def add_pairwise_xor(
    circuit: Circuit,
    x_labels: list[gate.Label],
    y_labels: list[gate.Label],
    *,
    result_labels: list[gate.Label] = None,
    add_outputs=False
) -> list[gate.Label]:
    if len(x_labels) != len(y_labels):
        raise PairwiseXorDifferentShapesError()

    n = len(x_labels)
    if result_labels is None:
        result_labels = []
        for i in range(n):
            result_labels.append(_get_new_label(circuit))

    if len(result_labels) != n:
        raise PairwiseXorDifferentShapesError()

    for i in range(n):
        circuit.add_gate(Gate(result_labels[i], gate.XOR, (x_labels[i], y_labels[i])))
        if add_outputs:
            circuit.mark_as_output(result_labels[i])
    return result_labels


def _generate_labels(prefix: str, n: int) -> list[str]:
    return [prefix + '_' + str(i) for i in range(n)]


def _get_new_label(circuit: Circuit) -> gate.Label:
    ans = "new_" + uuid.uuid4().hex
    while circuit.has_gate(ans):
        ans = "new_" + uuid.uuid4().hex
    return ans
