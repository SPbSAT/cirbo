import typing as tp

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.multiplication import (
    add_mul_karatsuba,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import (
    add_sum_pow2_m1,
    add_sum_two_numbers_with_shift,
)


__all__ = [
    'add_square',
    'add_square_pow2_m1',
]


def add_square(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    """
    Compute the square of a number represented by the given input labels in the circuit.

    :param circuit: The general circuit.
    :param input_labels: Iterable of gate labels representing the input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the square of the input number.

    """
    input_labels = list(input_labels)
    n = len(input_labels)
    if big_endian:
        input_labels.reverse()

    if n < 48 or n in [49, 53]:
        return reverse_if_big_endian(
            add_square_pow2_m1(circuit, input_labels), big_endian
        )

    mid = n // 2
    a = input_labels[:mid]
    b = input_labels[mid:]
    aa = add_square(circuit, a)
    bb = add_square(circuit, b)
    ab = add_mul_karatsuba(circuit, a, b)

    res = add_sum_two_numbers_with_shift(circuit, mid + 1, aa, ab)
    final_res = add_sum_two_numbers_with_shift(circuit, 2 * mid, res, bb)
    final_res = final_res[: 2 * n]
    return reverse_if_big_endian(final_res, big_endian)


def add_square_pow2_m1(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    """
    Compute the square of a number with length 2^k - 1 using a specific squaring method.

    :param circuit: The general circuit.
    :param input_labels: Iterable of gate labels representing the input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the square of the input number.
    """
    input_labels = list(input_labels)
    n = len(input_labels)
    if big_endian:
        input_labels.reverse()

    if n == 1:
        return reverse_if_big_endian(input_labels, big_endian)

    c = [[PLACEHOLDER_STR] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            c[i][j] = add_gate_from_tt(
                circuit,
                input_labels[i],
                input_labels[j],
                '0001',
            )
    for i in range(n):
        c[i][i] = input_labels[i]

    d = [[[PLACEHOLDER_STR]] for _ in range(2 * n)]
    d[0] = [[c[0][0]]]
    zero = add_gate_from_tt(
        circuit,
        input_labels[0],
        input_labels[0],
        '0000',
    )
    d[1] = [[zero]]
    for i in range(2, 2 * n):
        inp = []
        for j in range(i // 2):
            if j < n and -1 < i - j - 1 < n:
                inp.append(c[j][i - j - 1])
        if i % 2 == 0:
            inp.append(c[i // 2][i // 2])
        for j in range(i):
            if j + len(d[j]) > i:
                inp += d[j][i - j]
        if len(inp) == 1:
            d[i] = [[inp[0]]]
        else:
            d[i] = add_sum_pow2_m1(circuit, inp)
    res = [d[i][0][0] for i in range(2 * n)]
    if big_endian:
        res.reverse()
    return res
