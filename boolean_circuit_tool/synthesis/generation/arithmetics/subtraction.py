from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    validate_const_size,
    validate_equal_sizes,
)


__all__ = [
    "add_sub2",
    "add_sub3",
    "add_sub_two_numbers",
    "add_subtract_with_compare",
]


def add_sub2(circuit, input_labels):
    validate_const_size(input_labels, 2)
    [x1, x2] = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, x1, x2, '0100')

    return g1, g2  # res and balance


def add_sub3(circuit, input_labels):
    validate_const_size(input_labels, 3)
    x0, x1, x2 = input_labels  # A, B and balance (we do A - B)
    x3 = add_gate_from_tt(circuit, x0, x1, '0110')
    x4 = add_gate_from_tt(circuit, x1, x2, '0110')
    x5 = add_gate_from_tt(circuit, x3, x4, '0111')
    x6 = add_gate_from_tt(circuit, x2, x3, '0110')
    x7 = add_gate_from_tt(circuit, x0, x5, '0110')
    return x6, x7


def add_sub_two_numbers(circuit, input_labels_a, input_labels_b):
    """
    Function to subtract two binary numbers represented by input labels.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :return: List of bits representing the difference of the two numbers.

    """
    n = len(input_labels_a)
    m = len(input_labels_b)
    res = [0] * n
    bal = [0] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        if i < m:
            res[i], bal[i] = add_sub3(
                circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]]
            )
        else:
            res[i], bal[i] = add_sub2(circuit, [input_labels_a[i], bal[i - 1]])

    return res


def add_subtract_with_compare(
    circuit: Circuit,
    input_labels_a: list[gate.Label],
    input_labels_b: list[gate.Label],
) -> (list[gate.Label], gate.Label):
    """
    Subtracts given integer b from integer a and return residual bit representing if
    subtraction was successful (equivalent to a>=b).

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :return: tuple (labels that carry subtraction result, label of gate that carries
        residual bit)

    """
    validate_equal_sizes(input_labels_a, input_labels_b)

    n = len(input_labels_a)

    res = [0] * n
    bal = [0] * n

    res[0], bal[0] = add_sub2(
        circuit,
        [input_labels_a[0], input_labels_b[0]],
    )
    for i in range(1, n):
        res[i], bal[i] = add_sub3(
            circuit,
            [input_labels_a[i], input_labels_b[i], bal[i - 1]],
        )
    return res, bal[n - 1]
