import collections
import typing as tp

from boolean_circuit_tool.core.circuit import Circuit, gate

from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
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
]


def add_mul(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    # in my mind a[0] is the smallest bit in a
    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return [c[i][0] for i in range(m)]
    if m == 1:
        return c[0]

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
    return [d[i][0] for i in range(n + m)]


def add_mul_alter(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    # in my mind a[0] is the smallest bit in a
    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if m == 1:
        return c[0]

    res = add_sum_two_numbers_with_shift(circuit, 1, c[0], c[1])
    for i in range(2, m):
        res = add_sum_two_numbers_with_shift(circuit, i, res, c[i])

    return res


def add_mul_karatsuba(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:  # work on equal sizes
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
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
        return add_mul_pow2_m1(circuit, input_labels_a, input_labels_b)[:out_size]

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

    return final_res[:out_size]


def add_mul_dadda(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    c: list[tp.Deque[str]] = [collections.deque() for _ in range(n + m)]
    for i in range(m):
        for j in range(n):
            c[i + j].append(
                add_gate_from_tt(circuit, input_labels_a[j], input_labels_b[i], '0001')
            )

    if n == 1 or m == 1:
        return [c[i][0] for i in range(m + n - 1)]

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
    return out


def add_mul_wallace(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    c = [[PLACEHOLDER_STR] * m for _ in range(n + m)]
    for i in range(m):
        for j in range(n):
            c[i + j][i] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return [c[i][i] for i in range(m)]
    if m == 1:
        return [c[i][0] for i in range(n)]

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

    return add_sum_two_numbers_with_shift(circuit, shift, labels_a, labels_b)[: n + m]


def add_mul_pow2_m1(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    c = [[PLACEHOLDER_STR] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels_a[j], input_labels_b[i], '0001'
            )

    if n == 1:
        return [c[i][0] for i in range(m)]
    if m == 1:
        return c[0]

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
    return [out[i][0][0] for i in range(n + m)]
