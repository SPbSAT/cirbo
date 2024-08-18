import collections
import enum
import typing as tp

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.subtraction import (
    add_sub_two_numbers,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import (
    add_sum2,
    add_sum3,
    add_sum_n_bits,
    add_sum_pow2_m1,
    add_sum_two_numbers,
    add_sum_two_numbers_with_shift,
)


__all__ = [
    'add_mul',
    'add_mul_karatsuba',
    'add_mul_alter',
    'add_mul_dadda',
    'add_mul_wallace',
    'add_mul_pow2_m1',
    'generate_mul',
    'MulMode',
]


class MulMode(enum.Enum):
    DEFAULT = "DEFAULT"
    KARATSUBA = "KARATSUBA"
    ALTER = "ALTER"
    DADDA = "DADDA"
    WALLACE = "WALLACE"
    POW2_M1 = "POW2_M1"


def generate_mul(
    size_of_input_a: int,
    size_of_input_b: int,
    *,
    type: MulMode = MulMode.DEFAULT,
    big_endian: bool = False,
) -> Circuit:
    """
    Generates a circuit that have mul two numbers (one number is first `size_of_input_a`
    bits, other is second `size_of_input_b` bits) in result.

    :param size_of_input_a: the number of inputs representing the first number.
    :param size_of_input_b: the number of inputs representing the second number.
    :param type: what type of algorithm to use
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: circuit that product of the two input numbers.

    """

    circuit = Circuit.bare_circuit(size_of_input_a + size_of_input_b)
    outputs = _process_mul[type](
        circuit,
        circuit.inputs[:size_of_input_a],
        circuit.inputs[size_of_input_a:],
        big_endian=big_endian,
    )
    circuit.set_outputs(outputs)
    return circuit


def add_mul(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Multiplies two numbers represented by the given input labels using a straightforward
    bitwise multiplication method.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    # in my mind a[0] is the smallest bit in a
    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return reverse_if_big_endian([c[i][0] for i in range(m)], big_endian)
    if m == 1:
        return reverse_if_big_endian(c[0], big_endian)

    d = [[PLACEHOLDER_STR] for _ in range(n + m)]
    d[0] = [c[0][0]]
    for i in range(1, n + m):
        inp = []
        for j in range(i + 1):
            if j < m and i - j < n:
                inp.append(c[j][i - j])
        for j in range(i):
            if j + len(d[j]) > i:
                inp.append(d[j][i - j])
        d[i] = add_sum_n_bits(circuit, inp)
    return reverse_if_big_endian([d[i][0] for i in range(n + m)], big_endian)


def add_mul_alter(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    An alternative multiplication method using bitwise shifting and addition.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    # in my mind a[0] is the smallest bit in a
    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if m == 1:
        return reverse_if_big_endian(c[0], big_endian)

    res = add_sum_two_numbers_with_shift(circuit, 1, c[0], c[1])
    for i in range(2, m):
        res = add_sum_two_numbers_with_shift(circuit, i, res, c[i])

    return reverse_if_big_endian(res, big_endian)


def add_mul_karatsuba(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Multiplies two numbers using the Karatsuba multiplication algorithm.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()
    out_size = len(input_labels_a) + len(input_labels_b)
    if len(input_labels_a) == 1 or len(input_labels_b) == 1:
        out_size -= 1

    n = len(input_labels_a)
    if n < len(input_labels_b):
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
        n = len(input_labels_a)
    while n != len(input_labels_b):
        input_labels_b.append(
            add_gate_from_tt(circuit, input_labels_a[0], input_labels_a[0], '0110')
        )

    if n < 20 and n != 18:
        return reverse_if_big_endian(
            add_mul_pow2_m1(circuit, input_labels_a, input_labels_b)[:out_size],
            big_endian,
        )

    mid = n // 2
    a = input_labels_a[mid:]
    b = input_labels_a[:mid]
    c = input_labels_b[mid:]
    d = input_labels_b[:mid]

    ac = (
        add_mul_pow2_m1(circuit, a, c)
        if (n - mid < 20 and n - mid != 18)
        else add_mul_karatsuba(circuit, a, c)
    )
    bd = (
        add_mul_pow2_m1(circuit, b, d)
        if (mid < 20 and mid != 18)
        else add_mul_karatsuba(circuit, b, d)
    )
    a_sum_b = add_sum_two_numbers(circuit, a, b)
    c_sum_d = add_sum_two_numbers(circuit, c, d)
    big_mul = (
        add_mul_pow2_m1(circuit, a_sum_b, c_sum_d)
        if (len(a_sum_b) < 20 and len(a_sum_b) != 18)
        else add_mul_karatsuba(circuit, a_sum_b, c_sum_d)
    )
    ac_sum_bd = add_sum_two_numbers(circuit, ac, bd)
    res_mid = add_sub_two_numbers(circuit, big_mul, ac_sum_bd)

    res = add_sum_two_numbers_with_shift(circuit, mid, bd, res_mid)
    final_res = add_sum_two_numbers_with_shift(circuit, 2 * mid, res, ac)

    return reverse_if_big_endian(final_res[:out_size], big_endian)


def add_mul_dadda(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Multiplies two numbers using the Dadda multiplication algorithm.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    c: list[tp.Deque[str]] = [collections.deque() for _ in range(n + m)]
    for i in range(m):
        for j in range(n):
            c[i + j].append(
                add_gate_from_tt(circuit, input_labels_a[j], input_labels_b[i], '0001')
            )

    if n == 1 or m == 1:
        return reverse_if_big_endian([c[i][0] for i in range(m + n - 1)], big_endian)

    di = 2
    while 3 * di // 2 < min(n, m):
        di = 3 * di // 2

    while di != 1:
        for i in range(1, n + m):
            while len(c[i]) >= di:
                if len(c[i]) == di:
                    g1, g2 = add_sum2(circuit, [c[i].popleft(), c[i].popleft()])
                    c[i].append(g1)
                    if i + 1 < n + m:
                        c[i + 1].append(g2)
                else:
                    g1, g2 = add_sum3(
                        circuit, [c[i].popleft(), c[i].popleft(), c[i].popleft()]
                    )
                    c[i].append(g1)
                    if i + 1 < n + m:
                        c[i + 1].append(g2)
        if di == 2:
            di = 1
        else:
            di = (2 * di + 2) // 3

    out = []
    for i in range(n + m):
        out.append(c[i].popleft())
    return reverse_if_big_endian(out, big_endian)


def add_mul_wallace(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Multiplies two numbers using the Dadda multiplication algorithm.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    c = [[PLACEHOLDER_STR] * m for _ in range(n + m)]
    for i in range(m):
        for j in range(n):
            c[i + j][i] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return reverse_if_big_endian([c[i][i] for i in range(m)], big_endian)

    if m == 1:
        return reverse_if_big_endian([c[i][0] for i in range(n)], big_endian)

    while len(c[0]) != 2:
        cn = [[PLACEHOLDER_STR] * (2 * (len(c[0]) // 3)) for _ in range(n + m)]
        for row in range(0, len(c[0]) - len(c[0]) % 3, 3):
            for col in range(n + m):
                inp = []
                for k in range(row, row + 3):
                    if c[col][k] != PLACEHOLDER_STR:
                        inp.append(c[col][k])

                if len(inp) > 0:
                    res = add_sum_n_bits(circuit, inp)
                    for i in range(len(res)):
                        if col + i < n + m:
                            cn[col + i][2 * (row // 3) + i] = res[i]

        for row in range(len(c[0]) - len(c[0]) % 3, len(c[0])):
            for col in range(n + m):
                cn[col].append(c[col][row])

        c = cn

    labels_a = []
    labels_b = []
    shift = 0
    for i in range(n + m):
        if c[i][0] != PLACEHOLDER_STR:
            labels_a.append(c[i][0])
        if c[i][1] != PLACEHOLDER_STR:
            labels_b.append(c[i][1])
        elif len(labels_b) == 0:
            shift += 1

    return reverse_if_big_endian(
        add_sum_two_numbers_with_shift(circuit, shift, labels_a, labels_b)[: n + m],
        big_endian,
    )


def add_mul_pow2_m1(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Multiplies two numbers with lengths 2^k - 1 using a specific squaring method.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the first input number.
    :param input_labels_b: Iterable of gate labels representing the second input number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: A list of gate labels representing the product of the two input numbers.
    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return reverse_if_big_endian([c[i][0] for i in range(m)], big_endian)
    if m == 1:
        return reverse_if_big_endian(c[0], big_endian)

    out = [[[PLACEHOLDER_STR]] for _ in range(n + m)]
    out[0] = [[c[0][0]]]
    for i in range(1, n + m):
        inp = []
        for j in range(i + 1):
            if j < m and i - j < n:
                inp.append(c[j][i - j])
        for j in range(i):
            if j + len(out[j]) > i:
                inp += out[j][i - j]
        if len(inp) == 1:
            out[i] = [[inp[0]]]
        else:
            out[i] = add_sum_pow2_m1(circuit, inp)
    return reverse_if_big_endian([out[i][0][0] for i in range(n + m)], big_endian)


_process_mul: dict[MulMode, tp.Callable[..., list[gate.Label]]] = {
    MulMode.DEFAULT: add_mul,
    MulMode.KARATSUBA: add_mul_karatsuba,
    MulMode.ALTER: add_mul_alter,
    MulMode.DADDA: add_mul_dadda,
    MulMode.WALLACE: add_mul_wallace,
    MulMode.POW2_M1: add_mul_pow2_m1,
}
