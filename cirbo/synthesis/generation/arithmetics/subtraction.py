import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
    validate_const_size,
    validate_equal_sizes,
)


__all__ = [
    "add_sub2",
    "add_sub3",
    "add_sub_two_numbers",
    "add_subtract_with_compare",
    "generate_sub_two_numbers",
]


def generate_sub_two_numbers(
    size_of_input_a: int,
    size_of_input_b: int,
    *,
    big_endian: bool = False,
) -> Circuit:
    """
    Generates a circuit that have subtract two binary numbers in result.

    :param size_of_input_a: the number of inputs representing the first number.
    :param size_of_input_b: the number of inputs representing the second number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: circuit that difference of the two numbers.

    """

    circuit = Circuit.bare_circuit(size_of_input_a + size_of_input_b)
    outputs = add_sub_two_numbers(
        circuit,
        circuit.inputs[:size_of_input_a],
        circuit.inputs[size_of_input_a:],
        big_endian=big_endian,
    )
    circuit.set_outputs(outputs)
    return circuit


def add_sub2(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    input_labels = list(input_labels)
    if big_endian:
        input_labels.reverse()
    validate_const_size(input_labels, 2)
    [x1, x2] = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, x1, x2, '0100')

    return list([g1, g2])  # res and balance


def add_sub3(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    input_labels = list(input_labels)
    if big_endian:
        input_labels.reverse()
    validate_const_size(input_labels, 3)
    x0, x1, x2 = input_labels  # A, B and balance (we do A - B)
    x3 = add_gate_from_tt(circuit, x0, x1, '0110')
    x4 = add_gate_from_tt(circuit, x1, x2, '0110')
    x5 = add_gate_from_tt(circuit, x3, x4, '0111')
    x6 = add_gate_from_tt(circuit, x2, x3, '0110')
    x7 = add_gate_from_tt(circuit, x0, x5, '0110')
    return list([x6, x7])


def add_sub_two_numbers(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Function to subtract two binary numbers represented by input labels.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the difference of the two numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    res = [PLACEHOLDER_STR] * n
    bal = [PLACEHOLDER_STR] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        if i < m:
            res[i], bal[i] = add_sub3(
                circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]]
            )
        else:
            res[i], bal[i] = add_sub2(circuit, [input_labels_a[i], bal[i - 1]])

    return reverse_if_big_endian(res, big_endian)


def add_subtract_with_compare(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> tuple[list[gate.Label], gate.Label]:
    """
    Subtracts given integer b from integer a and return residual bit representing if
    subtraction was successful (equivalent to a>=b).

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: tuple (labels that carry subtraction result, label of gate that carries
        residual bit)

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)

    always_false = add_gate_from_tt(
        circuit, input_labels_a[0], input_labels_b[0], "0000"
    )
    while len(input_labels_a) < len(input_labels_b):
        input_labels_a.append(always_false)
    while len(input_labels_a) > len(input_labels_b):
        input_labels_b.append(always_false)

    validate_equal_sizes(input_labels_a, input_labels_b)

    n = len(input_labels_a)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    res = [PLACEHOLDER_STR] * n
    bal = [PLACEHOLDER_STR] * n

    res[0], bal[0] = add_sub2(
        circuit,
        [input_labels_a[0], input_labels_b[0]],
    )
    for i in range(1, n):
        res[i], bal[i] = add_sub3(
            circuit,
            [input_labels_a[i], input_labels_b[i], bal[i - 1]],
        )
    return reverse_if_big_endian(res, big_endian), bal[n - 1]
