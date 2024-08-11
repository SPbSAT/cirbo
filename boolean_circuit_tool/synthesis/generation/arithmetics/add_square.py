from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_mul import (
    add_mul,
    add_mul_karatsuba,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_n_bits_sum import (
    add_sum_pow2_m1,
    add_sum_two_numbers_with_shift,
)


def add_square(circuit, input_labels_a):
    n = len(input_labels_a)

    if n < 48 or n in [49, 53]:
        return add_square_pow2_m1(circuit, input_labels_a)

    mid = n // 2
    a = input_labels_a[:mid]
    b = input_labels_a[mid:]
    aa = add_square(circuit, a)
    bb = add_square(circuit, b)
    ab = add_mul_karatsuba(circuit, a, b)

    res = add_sum_two_numbers_with_shift(circuit, mid + 1, aa, ab)
    final_res = add_sum_two_numbers_with_shift(circuit, 2 * mid, res, bb)

    return final_res[: 2 * n]


def add_square_pow2_m1(circuit, input_labels):
    n = len(input_labels)

    if n == 1:
        return input_labels

    c = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            c[i][j] = add_gate_from_tt(
                circuit, input_labels[i], input_labels[j], '0001'
            )
    for i in range(n):
        c[i][i] = input_labels[i]

    d = [[0] for _ in range(2 * n)]
    d[0] = [[c[0][0]]]
    zero = add_gate_from_tt(circuit, input_labels[0], input_labels[0], '0000')
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
    return [d[i][0][0] for i in range(2 * n)]
