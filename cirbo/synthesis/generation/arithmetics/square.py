import collections
import enum
import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
)
from cirbo.synthesis.generation.arithmetics.multiplication import (
    add_fin_sum,
    add_mul_karatsuba,
)
from cirbo.synthesis.generation.arithmetics.summation import (
    add_sum2,
    add_sum3,
    add_sum_pow2_m1,
    add_sum_two_numbers_log_depth,
    add_sum_two_numbers_with_shift,
)
from cirbo.synthesis.generation.exceptions import BadBasisError
from cirbo.synthesis.generation.helpers import GenerationBasis


__all__ = [
    'add_square',
    'add_square_dadda',
    'add_square_pow2_m1',
    'generate_square',
    'SquareMode',
]


class SquareMode(enum.Enum):
    DEFAULT = "DEFAULT"
    POW2_M1 = "POW2_M1"
    DADDA = "DADDA"


def generate_square(
    number_inputs: int,
    *,
    type: SquareMode = SquareMode.DEFAULT,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> Circuit:
    """
    Generates a circuit that have square of number in result.

    :param number_inputs: number of input bits
    :param type: what type of algorithm to use
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A circuit whose outputs represent the square of the input number.

    """
    circuit = Circuit.bare_circuit(number_inputs)
    outputs = _process_square[type](
        circuit,
        circuit.inputs,
        big_endian=big_endian,
        basis=basis,
    )
    circuit.set_outputs(outputs)
    return circuit


def add_square(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Compute the square of a number represented by the given input labels in the circuit.

    :param circuit: The general circuit.
    :param input_labels: Iterable of gate labels representing the input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG].
    :return: A list of gate labels representing the square of the input number.

    """
    if basis != GenerationBasis.XAIG:
        raise BadBasisError("Only XAIG is supported for square")

    input_labels = list(input_labels)
    n = len(input_labels)
    if big_endian:
        input_labels.reverse()

    if n < 48 or n in [49, 53]:
        return reverse_if_big_endian(
            add_square_pow2_m1(circuit, input_labels, basis=basis), big_endian
        )

    mid = n // 2
    a = input_labels[:mid]
    b = input_labels[mid:]
    aa = add_square(circuit, a, basis=basis)
    bb = add_square(circuit, b, basis=basis)
    ab = add_mul_karatsuba(circuit, a, b)

    res = add_sum_two_numbers_with_shift(circuit, mid + 1, aa, ab)
    final_res = add_sum_two_numbers_with_shift(circuit, 2 * mid, res, bb)
    final_res = final_res[: 2 * n]
    return reverse_if_big_endian(final_res, big_endian)


def add_square_dadda(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    sum_func: tp.Callable[..., list[gate.Label]] = add_sum_two_numbers_log_depth,
    basis: GenerationBasis = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Computes the square of a number using the Dadda multiplication algorithm.

    :param circuit: The general circuit.
    :param input_labels: Iterable of gate labels representing the input number.
    :param sum_func: Function used to perform the final carry-propagate sum.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the square of the input number.

    """
    input_labels = list(input_labels)
    n = len(input_labels)

    if big_endian:
        input_labels.reverse()

    c: list[tp.Deque[str]] = [collections.deque() for _ in range(2 * n)]
    for i in range(n):
        for j in range(i + 1, n):
            c[i + j + 1].append(
                add_gate_from_tt(circuit, input_labels[i], input_labels[j], '0001')
            )
    for i in range(n):
        c[2 * i].append(input_labels[i])

    if n == 1:
        return reverse_if_big_endian([c[i][0] for i in range(2 * n - 1)], big_endian)

    di = 2
    while 3 * di // 2 < n:
        di = 3 * di // 2

    while di != 1:
        for i in range(2, 2 * n):
            while len(c[i]) > di:
                if len(c[i]) == di + 1:
                    g1, g2 = add_sum2(
                        circuit, [c[i].popleft(), c[i].popleft()], basis=basis
                    )
                    c[i].append(g1)
                    if i + 1 < 2 * n:
                        c[i + 1].append(g2)
                else:
                    g1, g2 = add_sum3(
                        circuit,
                        [c[i].popleft(), c[i].popleft(), c[i].popleft()],
                        basis=basis,
                    )
                    c[i].append(g1)
                    if i + 1 < 2 * n:
                        c[i + 1].append(g2)
        if di == 2:
            di = 1
        else:
            di = (2 * di + 2) // 3

    out = add_fin_sum(circuit, c, sum_func=sum_func, basis=basis)[: 2 * n]
    return reverse_if_big_endian(out, big_endian)


def add_square_pow2_m1(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Compute the square of a number with length 2^k - 1 using a specific squaring method.

    :param circuit: The general circuit.
    :param input_labels: Iterable of gate labels representing the input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
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
            d[i] = add_sum_pow2_m1(circuit, inp, basis=basis)
    res = [d[i][0][0] for i in range(2 * n)]
    return reverse_if_big_endian(res, big_endian)


_process_square: dict[SquareMode, tp.Callable[..., list[gate.Label]]] = {
    SquareMode.DEFAULT: add_square,
    SquareMode.POW2_M1: add_square_pow2_m1,
    SquareMode.DADDA: add_square_dadda,
}
