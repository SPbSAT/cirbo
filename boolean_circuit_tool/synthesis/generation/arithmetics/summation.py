import typing as tp
from itertools import zip_longest

from boolean_circuit_tool.core.circuit import Circuit, gate

from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
    validate_const_size,
)
from boolean_circuit_tool.synthesis.generation.exceptions import BadBasisError
from boolean_circuit_tool.synthesis.generation.helpers import GenerationBasis


__all__ = [
    "generate_sum_n_bits",
    "add_sum2",
    "add_sum3",
    "add_sum_n_bits",
    "add_sum_n_bits_easy",
    "add_sum_pow2_m1",
    "add_sum_two_numbers",
    "add_sum_two_numbers_with_shift",
]


def add_sum_two_numbers(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Function to add two binary numbers represented by input labels.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the sum of the two numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if n < m:
        n, m = m, n
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
    d = [[PLACEHOLDER_STR] for _ in range(n + 1)]
    d[0] = add_sum_n_bits(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        inp = [d[i - 1][1], input_labels_a[i]]
        if i < m:
            inp.append(input_labels_b[i])
        d[i] = list(add_sum_n_bits(circuit, inp))
    d[n] = [d[n - 1][1]]
    return reverse_if_big_endian([d[i][0] for i in range(n + 1)], big_endian)


def add_sum_two_numbers_with_shift(
    circuit: Circuit,
    shift,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:  # shift for second
    """
    Function to add two binary numbers with a shift applied to the second number.

    :param circuit: The general circuit.
    :param shift: The number of bit positions to shift the second number.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the sum of the two numbers after applying the
        shift.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if (
        shift >= n
    ):  # if shift so big for first number (in out cases I hope we will not use this)
        d = [[PLACEHOLDER_STR] for _ in range(m + shift)]
        for i in range(n):
            d[i] = [input_labels_a[i]]
        if shift != n:
            zero = add_gate_from_tt(
                circuit,
                input_labels_a[0],
                input_labels_a[0],
                '0000',
            )
            for i in range(n, shift - n):
                d[i] = [zero]
        for i in range(m):
            d[i + shift] = [input_labels_b[i]]
        return reverse_if_big_endian([i[0] for i in d], big_endian)
    d = [[PLACEHOLDER_STR] for _ in range(max(n, m + shift) + 1)]
    for i in range(shift):
        d[i] = [input_labels_a[i]]
    res_sum = add_sum_two_numbers(circuit, input_labels_a[shift:n], input_labels_b)
    for i in range(shift, max(n, m + shift) + 1):
        d[i] = [res_sum[i - shift]]
    return reverse_if_big_endian(
        [d[i][0] for i in range(max(n, m + shift) + 1)], big_endian
    )


def add_sum2(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 2)
    [x1, x2] = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    return list([g1, g2])


def add_sum3(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x3 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, g1, x3, '0110')
    g3 = add_gate_from_tt(circuit, x1, x2, '0001')
    g4 = add_gate_from_tt(circuit, g1, x3, '0001')
    g5 = add_gate_from_tt(circuit, g3, g4, '0110')
    return list([g2, g5])


# given x1, x2, and (x2 oplus x3), computes the binary representation
# of (x1 + x2 + x3)
def add_stockmeyer_block(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x23 = input_labels
    w0 = add_gate_from_tt(circuit, x1, x23, '0110')
    g2 = add_gate_from_tt(circuit, x2, x23, '0010')
    g3 = add_gate_from_tt(circuit, x1, x23, '0001')
    w1 = add_gate_from_tt(circuit, g2, g3, '0110')
    return list([w0, w1])


def add_mdfa(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 5)
    z, x1, xy1, x2, xy2 = input_labels
    g1 = add_gate_from_tt(circuit, x1, z, '0110')
    g2 = add_gate_from_tt(circuit, xy1, g1, '0111')
    g3 = add_gate_from_tt(circuit, xy1, z, '0110')
    g4 = add_gate_from_tt(circuit, g2, g3, '0110')
    g5 = add_gate_from_tt(circuit, x2, g3, '0110')
    g6 = add_gate_from_tt(circuit, g3, xy2, '0110')
    g7 = add_gate_from_tt(circuit, g5, xy2, '0010')
    g8 = add_gate_from_tt(circuit, g2, g7, '0110')
    return list([g6, g4, g8])


# an MDFA block with z=0
def add_simplified_mdfa(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 4)
    x1, xy1, x2, xy2 = input_labels
    g2 = add_gate_from_tt(circuit, xy1, x1, '0111')
    g4 = add_gate_from_tt(circuit, g2, xy1, '0110')
    g5 = add_gate_from_tt(circuit, x2, xy1, '0110')
    g6 = add_gate_from_tt(circuit, xy1, xy2, '0110')
    g7 = add_gate_from_tt(circuit, g5, xy2, '0010')
    g8 = add_gate_from_tt(circuit, g2, g7, '0110')
    return list([g6, g4, g8])


def add_sum_n_bits_easy(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    """
    Function to add a variable number of bits with numbers of gate approximately 5 * n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: Tuple containing the sum in binary representation.

    """
    now = list(input_labels)
    if big_endian:
        now.reverse()
    res = []
    while len(now) > 0:
        next = []
        while len(now) > 2:
            x, y = add_sum3(circuit, now[-1:-4:-1])
            for _ in range(3):
                now.pop()
            now.append(x)
            next.append(y)
        while len(now) > 1:
            x, y = add_sum2(circuit, now[-1:-3:-1])
            for _ in range(2):
                now.pop()
            now.append(x)
            next.append(y)
        res.append(now[0])
        now = next
    return reverse_if_big_endian(res, big_endian)


def add_sum2_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 2)
    x1, x2 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0111')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    g3 = add_gate_from_tt(circuit, g1, g2, '0010')
    return list([g3, g2])


def add_sum3_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x3 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0111')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    g3 = add_gate_from_tt(circuit, g1, g2, '0010')
    g4 = add_gate_from_tt(circuit, g3, x3, '0111')
    g5 = add_gate_from_tt(circuit, g3, x3, '0001')
    g6 = add_gate_from_tt(circuit, g4, g5, '0010')
    g7 = add_gate_from_tt(circuit, g2, g5, '0111')
    return list([g6, g7])


def generate_sum_n_bits(
    n: int,
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.ALL,
    big_endian: bool = False,
) -> Circuit:
    """
    Generates a circuit that have sum of n bits in result.

    :param n: number of input bits (must be even)
    :param basis: in which basis should generated function lie. Supported [ALL, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format

    """
    circuit = Circuit.bare_circuit(n)
    res = add_sum_n_bits(
        circuit,
        circuit.inputs,
        basis=basis,
        big_endian=big_endian,
    )
    circuit.set_outputs(res)
    return circuit


def add_sum_n_bits(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.ALL,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Function that adds summation gadget to a `circuit`.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :param basis: in which basis should generated function lie. Supported [ALL, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: list containing labels of sum bits.

    """

    input_labels = list(input_labels)
    if big_endian:
        input_labels.reverse()

    if isinstance(basis, str):
        _basis = GenerationBasis(basis.upper())
    else:
        _basis = basis

    if _basis == GenerationBasis.ALL:
        return reverse_if_big_endian(
            _add_sum_n_bits(
                circuit=circuit,
                input_labels=input_labels,
            ),
            big_endian,
        )
    if _basis == GenerationBasis.AIG:
        return reverse_if_big_endian(
            _add_sum_n_bits_aig(
                circuit=circuit,
                input_labels=input_labels,
            ),
            big_endian,
        )
    raise BadBasisError(f"Unsupported basis: {basis}.")


def _add_sum_n_bits_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    """
    Function to add a variable number of bits IN AIG basis with numbers of gate
    approximately 7 * n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :return: Tuple containing the sum in binary representation.

    """
    now = list(input_labels)
    res = []
    while len(now) > 0:
        next = []
        while len(now) > 2:
            x, y = add_sum3_aig(circuit, now[-1:-4:-1])
            for _ in range(3):
                now.pop()
            now.append(x)
            next.append(y)
        if len(now) > 1:
            x, y = add_sum2_aig(circuit, now[-1:-3:-1])
            for _ in range(2):
                now.pop()
            now.append(x)
            next.append(y)
        res.append(now[0])
        now = next
    return res


def _add_sum_n_bits(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    """
    Function to add a variable number of bits with numbers of gate approximately 4.5 *
    n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :return: Tuple containing the sum in binary representation.

    """
    res = []
    now_x_xy = []
    now_solo = list(input_labels)
    while len(now_solo) > 1:
        xy = add_gate_from_tt(circuit, now_solo[-1], now_solo[-2], "0110")
        now_x_xy.append((now_solo[-1], xy))
        for _ in range(2):
            now_solo.pop()

    while len(now_solo) > 0 or len(now_x_xy) > 0:
        next_solo = []
        next_x_xy = []
        while len(now_x_xy) > 1:
            if len(now_solo) > 0:
                z, x1, x1y1 = add_mdfa(
                    circuit,
                    [
                        now_solo[-1],
                        now_x_xy[-1][0],
                        now_x_xy[-1][1],
                        now_x_xy[-2][0],
                        now_x_xy[-2][1],
                    ],
                )
                for _ in range(2):
                    now_x_xy.pop()
                now_solo.pop()

                now_solo.append(z)
                next_x_xy.append((x1, x1y1))
            else:
                z, x1, x1y1 = add_simplified_mdfa(
                    circuit,
                    [
                        now_x_xy[-1][0],
                        now_x_xy[-1][1],
                        now_x_xy[-2][0],
                        now_x_xy[-2][1],
                    ],
                )
                for _ in range(2):
                    now_x_xy.pop()

                now_solo.append(z)
                next_x_xy.append((x1, x1y1))
        if len(now_x_xy) == 1:
            if len(now_solo) > 0:
                x, y = add_stockmeyer_block(
                    circuit, [now_solo[-1], now_x_xy[-1][0], now_x_xy[-1][1]]
                )
                now_solo.pop()
                now_x_xy.pop()
                next_solo.append(y)
                now_solo.append(x)
            else:
                now_solo.append(now_x_xy[-1][1])
                next_solo.append(
                    add_gate_from_tt(circuit, now_x_xy[-1][0], now_x_xy[-1][1], "0010")
                )
                now_x_xy.pop()

        while len(now_solo) > 2:
            x, y = add_sum3(circuit, now_solo[-1:-4:-1])
            for _ in range(3):
                now_solo.pop()
            now_solo.append(x)
            next_solo.append(y)
        if len(now_solo) > 1:
            x, y = add_sum2(circuit, now_solo[-1:-3:-1])
            for _ in range(2):
                now_solo.pop()
            now_solo.append(x)
            next_solo.append(y)
        res.append(now_solo[0])
        now_solo = next_solo
        now_x_xy = next_x_xy
    return res


# divides the sum into blocks of size 2^n-1
# will be replaced with calls of 4.5n sums generator
def add_sum_pow2_m1(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[list[gate.Label]]:
    input_labels = list(input_labels)
    n = len(input_labels)
    assert n > 0
    if n == 1:
        return [reverse_if_big_endian([input_labels[0]], big_endian)]

    out = []
    it = 0
    while len(input_labels) > 2:
        for pw in range(5, 1, -1):
            i = 2**pw - 1
            while len(input_labels) >= i:
                out.append(add_sum_n_bits(circuit, input_labels[0:i]))
                input_labels = input_labels[i:]
                input_labels.append(out[it][0])
                it += 1
    if len(input_labels) == 2:
        out.append(add_sum2(circuit, input_labels[0:2]))
        input_labels = input_labels[2:]
        input_labels.append(out[it][0])

    out = [list(filter(None, x)) for x in zip_longest(*out)]
    out[0] = [out[0][len(out[0]) - 1]]
    return [reverse_if_big_endian(i, big_endian) for i in out]
