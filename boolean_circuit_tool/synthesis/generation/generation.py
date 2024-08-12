"""Module defines several general, including generation of "plus-one" circuit, "it-then-
else" gadget  and "pairwise xor", useful for miter construction."""

import typing as tp
import uuid

from boolean_circuit_tool.core.circuit import Circuit, Gate, gate
from boolean_circuit_tool.synthesis.generation.exceptions import (
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

LITTLE_ENDIAN = 'little_endian'
BIG_ENDIAN = 'big_endian'


def generate_plus_one(
    inp_len: int, out_len: int, *, endianness=LITTLE_ENDIAN
) -> Circuit:
    """
    Generates a circuit that adds 1 to a number of `inp_len` bits and returns `out_len`
    least-significant bits of the result.

    :param inp_len: number of input bits
    :param out_len: number of output bits
    :param endianness: defines how to interpret numbers, big-endian or little-endian
        format

    """
    x_labels = _generate_labels('x', inp_len)[::-1]
    z_labels = _generate_labels('z', out_len)[::-1]
    circuit = Circuit()
    circuit.add_inputs(x_labels)

    add_plus_one(
        circuit,
        x_labels,
        result_labels=z_labels,
        add_outputs=True,
        endianness=endianness,
    )
    return circuit


def generate_if_then_else() -> Circuit:
    """Generates a circuit that computes `if then else` function of three bits."""
    circuit = Circuit()
    circuit.add_inputs(['if', 'then', 'else'])

    add_if_then_else(
        circuit, 'if', 'then', 'else', result_label='if_then_else', add_outputs=True
    )
    return circuit


def generate_pairwise_if_then_else(n: int) -> Circuit:
    """
    Generates a circuit with `3n` inputs `[if_0, .., if_{n-1}, then_0, .., then_{n-1},
    else_0, ..., else_{n-1}]` and `n` outputs `[if_then_else_0, .., if_then_else_{n-1}]`
    that computes `if then else` function for every 0 <= i < n.

    :param n: 3n -- number of inputs, n -- number of outputs

    """
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
    """
    Generates a circuit with `2n` inputs `[x_0, .., x_{n-1}, y_0, .., y_{n-1}]` and `n`
    outputs `[xor_0, .., xor_{n-1}]` that computes `xor` function for every 0 <= i < n.

    :param n: 2n -- number of inputs, n -- number of outputs

    """
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
    """
    Generates a circuit consisting of INPUT gates with given labels. Those gates are
    also marked as OUTPUTS.

    :param labels: names for the input gates

    """
    circuit = Circuit()
    circuit.add_inputs(labels)
    circuit.set_outputs(labels)
    return circuit


def generate_inputs(n: int) -> Circuit:
    """
    Generates a circuit consisting of n INPUT gates. Those gates are also marked as
    OUTPUTS.

    :param n: number of input gates

    """
    return generate_inputs_with_labels(_generate_labels('x', n))


def add_plus_one(
    circuit: Circuit,
    input_labels: list[gate.Label],
    *,
    result_labels: tp.Optional[list[gate.Label]] = None,
    add_outputs=False,
    endianness=LITTLE_ENDIAN,
) -> list[gate.Label]:
    """
    For a given circuit, adds a subcircuit that adds 1 to a number corresponding to the
    given input gates, and returns least-significant bits of the result.

    :param circuit: base circuit
    :param input_labels: labels of gates of the circuit that will be inputs of the new
        subcircuit
    :param result_labels: (optional parameter) labels that will correspond to the
        outputs of the new subcircuit
    :param add_outputs: (optional parameter) indicates whether the outputs of the new
        subcircuit are added to the outputs of the circuit
    :param endianness: defines how to interpret numbers, big-endian or little-endian
        format
    :return: labels that correspond to the outputs of the new subcircuit

    """
    inp_len = len(input_labels)

    if result_labels is None:
        result_labels = []
        for i in range(inp_len + 1):
            result_labels.append(_get_new_label(circuit))

    if endianness == BIG_ENDIAN:
        input_labels = input_labels[::-1]
        result_labels = result_labels[::-1]

    out_len = len(result_labels)

    carries = _get_new_labels(circuit, out_len, other_restrictions=result_labels)
    circuit.add_gate(Gate(carries[0], gate.IFF, (input_labels[0],)))
    circuit.add_gate(
        Gate(result_labels[0], gate.NOT, (input_labels[0],))
    ).mark_as_output(result_labels[0])

    for i in range(1, out_len):
        if i < inp_len:
            if i < out_len - 1:
                circuit.add_gate(
                    Gate(
                        carries[i],
                        gate.AND,
                        (input_labels[i], carries[i - 1]),
                    )
                )
            circuit.add_gate(
                Gate(result_labels[i], gate.XOR, (input_labels[i], carries[i - 1]))
            )
        elif i == inp_len:
            circuit.add_gate(Gate(result_labels[i], gate.IFF, (carries[i - 1],)))
        else:
            circuit.add_gate(Gate(result_labels[i], gate.ALWAYS_FALSE, tuple()))
        if add_outputs:
            circuit.mark_as_output(result_labels[i])

    if endianness == BIG_ENDIAN:
        input_labels = input_labels[::-1]
        result_labels = result_labels[::-1]

    circuit.order_inputs(input_labels)
    circuit.order_outputs(result_labels)
    return result_labels


def add_if_then_else(
    circuit: Circuit,
    if_label: gate.Label,
    then_label: gate.Label,
    else_label: gate.Label,
    *,
    result_label: tp.Optional[gate.Label] = None,
    add_outputs=False,
) -> gate.Label:
    """
    For a given circuit, adds a subcircuit that computes `if then else` function of
    three given input gates.

    :param circuit: base circuit
    :param if_label: label of a gate of the circuit that will be if-input of the new
        subcircuit
    :param then_label: label of a gate of the circuit that will be then-input of the new
        subcircuit
    :param else_label: label of a gate of the circuit that will be else-input of the new
        subcircuit
    :param result_label: (optional parameter) label that will correspond to the outputs
        of the new subcircuit
    :param add_outputs: (optional parameter) indicates whether the output of the new
        subcircuit is added to the outputs of the circuit
    :return: label that correspond to the outputs of the new subcircuit

    """
    if result_label is None:
        result_label = _get_new_label(circuit)

    tmp = _get_new_labels(circuit, 3, other_restrictions=[result_label])
    circuit.add_gate(Gate(tmp[0], gate.AND, (if_label, then_label)))
    circuit.add_gate(Gate(tmp[1], gate.NOT, (if_label,)))
    circuit.add_gate(Gate(tmp[2], gate.AND, (tmp[1], else_label)))
    circuit.add_gate(Gate(result_label, gate.OR, (tmp[0], tmp[2])))
    if add_outputs:
        circuit.mark_as_output(result_label)

    return result_label


def add_pairwise_if_then_else(
    circuit: Circuit,
    if_labels: list[gate.Label],
    then_labels: list[gate.Label],
    else_labels: list[gate.Label],
    *,
    result_labels: tp.Optional[list[gate.Label]] = None,
    add_outputs=False,
) -> list[gate.Label]:
    """
    For a given circuit, adds a subcircuit with `3n` given inputs `if`, `then` and
    `else`, and `n` outputs, that computes `if then else` function of `(if[i], then[i],
    else[i])` for every 0 <= i < n.

    :param circuit: base circuit
    :param if_labels: labels of gates of the circuit that will be if-inputs of the new
        subcircuit
    :param then_labels: labels of gates of the circuit that will be then-inputs of the
        new subcircuit
    :param else_labels: labels of gates of the circuit that will be else-inputs of the
        new subcircuit
    :param result_labels: (optional parameter) labels that will correspond to the
        outputs of the new subcircuit
    :param add_outputs: (optional parameter) indicates whether the outputs of the new
        subcircuit are added to the outputs of the circuit
    :return: labels that correspond to the outputs of the new subcircuit

    """
    if len(if_labels) != len(then_labels) or len(then_labels) != len(else_labels):
        raise PairwiseIfThenElseDifferentShapesError()

    n = len(if_labels)
    if result_labels is None:
        result_labels = []
        for i in range(n):
            result_labels.append(_get_new_label(circuit))

    if len(result_labels) != n:
        raise PairwiseIfThenElseDifferentShapesError()

    for i in range(n):
        add_if_then_else(
            circuit,
            if_labels[i],
            then_labels[i],
            else_labels[i],
            result_label=result_labels[i],
            add_outputs=add_outputs,
        )

    return result_labels


def add_pairwise_xor(
    circuit: Circuit,
    x_labels: list[gate.Label],
    y_labels: list[gate.Label],
    *,
    result_labels: tp.Optional[list[gate.Label]] = None,
    add_outputs=False,
) -> list[gate.Label]:
    """
    For a given circuit, adds a subcircuit with `2n` given inputs `x` and `y`, and `n`
    outputs, that computes `x[i] xor y[i]` for every 0 <= i < n.

    :param circuit: base circuit
    :param x_labels: labels of gates of the circuit that will be x-inputs of the new
        subcircuit
    :param y_labels: labels of gates of the circuit that will be y-inputs of the new
        subcircuit
    :param result_labels: (optional parameter) labels that will correspond to the
        outputs of the new subcircuit
    :param add_outputs: (optional parameter) indicates whether the outputs of the new
        subcircuit are added to the outputs of the circuit
    :return: labels that correspond to the outputs of the new subcircuit

    """
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


def _get_new_label(
    circuit: Circuit,
    *,
    other_restrictions: tp.Optional[list[gate.Label]] = None,
) -> gate.Label:
    if other_restrictions is None:
        other_restrictions = []
    ans = "new_" + uuid.uuid4().hex
    while circuit.has_gate(ans) or ans in other_restrictions:
        ans = "new_" + uuid.uuid4().hex
    return ans


def _get_new_labels(
    circuit: Circuit,
    n: int,
    *,
    other_restrictions: tp.Optional[list[gate.Label]] = None,
) -> list[gate.Label]:
    if other_restrictions is None:
        other_restrictions = []
    ans: list[gate.Label] = []
    for i in range(n):
        ans.append(_get_new_label(circuit, other_restrictions=other_restrictions + ans))
    return ans
