from boolean_circuit_tool.core.circuit import Circuit, Gate
from itertools import product, zip_longest

from boolean_circuit_tool.core.circuit.gate import Gate, INPUT
from boolean_circuit_tool.generation.arithmetics.add_gate_from_TT import add_gate_with_TT


def add_sum_two_numbers(circuit, input_labels_a, input_labels_b):
    n = len(input_labels_a)
    m = len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    if n < m:
        n, m = m, n
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
    d = [[0] for _ in range(n + 1)]
    d[0] = add_sum(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        inp = [d[i - 1][1], input_labels_a[i]]
        if i < m:
            inp.append(input_labels_b[i])
        d[i] = list(add_sum(circuit, inp))
    d[n] = [d[n - 1][1]]
    return [d[i][0] for i in range(n + 1)]


def add_sum_two_numbers_with_shift(circuit, shift, input_labels_a, input_labels_b):  # shift for second
    n = len(input_labels_a)
    m = len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    if shift >= n:  # if shift so big for first number (in out cases I hope we will not use this)
        d = [[0] for _ in range(m + shift)]
        for i in range(n):
            d[i] = [input_labels_a[i]]
        if shift != n:
            zero = add_gate_with_TT(circuit, input_labels_a[0], input_labels_a[0], '0000')
            for i in range(n, shift - n):
                d[i] = [zero]
        for i in range(m):
            d[i + shift] = [input_labels_b[i]]
        return [i[0] for i in d]
    d = [[0] for _ in range(max(n, m + shift) + 1)]
    for i in range(shift):
        d[i] = [input_labels_a[i]]
    res_sum = add_sum_two_numbers(circuit, input_labels_a[shift:n], input_labels_b)
    for i in range(shift, max(n, m + shift) + 1):
        d[i] = [res_sum[i - shift]]
    return [d[i][0] for i in range(max(n, m + shift) + 1)]


def add_sum2(circuit, input_labels):
    assert len(input_labels) == 2
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2] = input_labels
    g1 = add_gate_with_TT(circuit, x1, x2, '0110')
    g2 = add_gate_with_TT(circuit, x1, x2, '0001')

    return g1, g2


def add_sum3(circuit, input_labels):
    assert len(input_labels) == 3
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3 = input_labels

    g1 = add_gate_with_TT(circuit, x1, x2, '0110')
    g2 = add_gate_with_TT(circuit, g1, x3, '0110')
    g3 = add_gate_with_TT(circuit, x1, x2, '0001')
    g4 = add_gate_with_TT(circuit, g1, x3, '0001')
    g5 = add_gate_with_TT(circuit, g3, g4, '0110')
    return g2, g5


def add_sub2(circuit, input_labels):
    assert len(input_labels) == 2
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2] = input_labels
    g1 = add_gate_with_TT(circuit, x1, x2, '0110')
    g2 = add_gate_with_TT(circuit, x1, x2, '0100')

    return g1, g2  # res and balance


def add_sub3(circuit, input_labels):
    assert len(input_labels) == 3
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x0, x1, x2 = input_labels  # A, B and balance (we do A - B)

    x3 = add_gate_with_TT(circuit, x0, x1, '0110')
    x4 = add_gate_with_TT(circuit, x1, x2, '0110')
    x5 = add_gate_with_TT(circuit, x3, x4, '0111')
    x6 = add_gate_with_TT(circuit, x2, x3, '0110')
    x7 = add_gate_with_TT(circuit, x0, x5, '0110')
    return x6, x7


def add_sub_two_numbers(circuit, input_labels_a, input_labels_b):
    n = len(input_labels_a)
    m = len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    res = [0] * n
    bal = [0] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        if i < m:
            res[i], bal[i] = add_sub3(circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]])
        else:
            res[i], bal[i] = add_sub2(circuit, [input_labels_a[i], bal[i - 1]])

    return res


# given x1, x2, and (x2 oplus x3), computes the binary representation
# of (x1 + x2 + x3)
def add_stockmeyer_block(circuit, input_labels):
    assert len(input_labels) == 3
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x23 = input_labels

    w0 = add_gate_with_TT(circuit, x1, x23, '0110')

    g2 = add_gate_with_TT(circuit, x2, x23, '0010')
    g3 = add_gate_with_TT(circuit, x1, x23, '0001')
    w1 = add_gate_with_TT(circuit, g2, g3, '0110')
    return w0, w1


def add_sum4(circuit, input_labels):
    assert len(input_labels) == 4
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4] = input_labels

    a0, a1 = add_sum3(circuit, [x1, x2, x3])
    w0, b1 = add_sum2(circuit, [a0, x4])
    w1, w2 = add_sum2(circuit, [a1, b1])

    return w0, w1, w2


def add_sum5_size11(circuit, input_labels):
    assert len(input_labels) == 5
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5] = input_labels

    g1 = add_gate_with_TT(circuit, x1, x2, '0110')
    g2 = add_gate_with_TT(circuit, x2, x3, '0110')
    g3 = add_gate_with_TT(circuit, g1, g2, '0111')
    g4 = add_gate_with_TT(circuit, g1, x3, '0110')
    g5 = add_gate_with_TT(circuit, g3, g4, '0110')
    g6 = add_gate_with_TT(circuit, x4, g4, '0110')
    g7 = add_gate_with_TT(circuit, x4, x5, '0110')
    g8 = add_gate_with_TT(circuit, g6, g7, '0010')
    g9 = add_gate_with_TT(circuit, g4, g7, '0110')
    g10 = add_gate_with_TT(circuit, g3, g8, '0110')
    g11 = add_gate_with_TT(circuit, g5, g10, '0010')

    return g9, g10, g11


def add_sum5_size11_via_mdfa(circuit, input_labels):
    assert len(input_labels) == 5
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5 = input_labels

    x23 = add_gate_with_TT(circuit, x2, x3, '0110')
    x45 = add_gate_with_TT(circuit, x4, x5, '0110')
    w0, c1, c12 = add_mdfa(circuit, [x1, x2, x23, x4, x45])
    w2 = add_gate_with_TT(circuit, c1, c12, '0010')

    return w0, c12, w2


def add_sum5_size12(circuit, input_labels):
    assert len(input_labels) == 5
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5] = input_labels

    a0, a1 = add_sum3(circuit, [x1, x2, x3])
    w0, b1 = add_sum3(circuit, [a0, x4, x5])
    w1, w2 = add_sum2(circuit, [a1, b1])

    return w0, w1, w2


def add_sum6_size16(circuit, input_labels):
    assert len(input_labels) == 6
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5, x6] = input_labels

    a0, a1, a2 = add_sum5_size11(circuit, [x1, x2, x3, x4, x5])
    w0, c1 = add_sum2(circuit, [a0, x6])
    w1, c2 = add_sum2(circuit, [a1, c1])
    w2 = add_gate_with_TT(circuit, a2, c2, '0110')

    return w0, w1, w2


def add_sum7_size19(circuit, input_labels):
    assert len(input_labels) == 7
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5, x6, x7] = input_labels

    a0, a1, a2 = add_sum5_size11(circuit, [x1, x2, x3, x4, x5])
    w0, c1 = add_sum3(circuit, [a0, x6, x7])
    w1, e1 = add_sum2(circuit, [a1, c1])
    w2 = add_gate_with_TT(circuit, a2, e1, '0110')

    return w0, w1, w2


def add_sum8_size25(circuit, input_labels):
    assert len(input_labels) == 8
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8 = input_labels

    x12 = add_gate_with_TT(circuit, x1, x2, '0110')
    x34 = add_gate_with_TT(circuit, x3, x4, '0110')
    x56 = add_gate_with_TT(circuit, x5, x6, '0110')
    x78 = add_gate_with_TT(circuit, x7, x8, '0110')
    a0, a1, a12 = add_simplified_mdfa(circuit, [x1, x12, x3, x34])
    w0, b1, b12 = add_mdfa(circuit, [a0, x5, x56, x7, x78])
    w1, c2, c23 = add_simplified_mdfa(circuit, [a1, a12, b1, b12])
    w3 = add_gate_with_TT(circuit, c2, c23, '0010')

    return w0, w1, c23, w3


def add_sum9_size27(circuit, input_labels):
    assert len(input_labels) == 9
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5, x6, x7, x8, x9] = input_labels

    a0, a1, a2 = add_sum5_size11(circuit, [x1, x2, x3, x4, x5])
    w0, b1, b2 = add_sum5_size11(circuit, [a0, x6, x7, x8, x9])

    w1 = add_gate_with_TT(circuit, a1, b1, '0110')
    d1 = add_gate_with_TT(circuit, a1, b1, '0001')
    d2 = add_gate_with_TT(circuit, a2, b2, '0110')
    d3 = add_gate_with_TT(circuit, d1, d2, '0110')
    d4 = add_gate_with_TT(circuit, a2, b2, '0001')

    return w0, w1, d3, d4


def add_sum10_size31(circuit, input_labels):
    assert len(input_labels) == 10
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10 = input_labels

    x34 = add_gate_with_TT(circuit, x3, x4, '0110')
    x56 = add_gate_with_TT(circuit, x5, x6, '0110')
    x78 = add_gate_with_TT(circuit, x7, x8, '0110')
    x910 = add_gate_with_TT(circuit, x9, x10, '0110')

    a0, a1 = add_sum2(circuit, [x1, x2])
    b0, b1, b12 = add_mdfa(circuit, [a0, x3, x34, x5, x56])
    c0, c1, c12 = add_mdfa(circuit, [b0, x7, x78, x9, x910])
    d1, d2, d23 = add_mdfa(circuit, [a1, b1, b12, c1, c12])
    w3 = add_gate_with_TT(circuit, d2, d23, '0010')

    return c0, d1, d23, w3


def add_sum11_size34(circuit, input_labels):
    assert len(input_labels) == 11
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11 = input_labels

    a0, a1 = add_sum3(circuit, [x1, x2, x3])

    x45 = add_gate_with_TT(circuit, x4, x5, '0110')
    x67 = add_gate_with_TT(circuit, x6, x7, '0110')
    c0, c1, c12 = add_mdfa(circuit, [a0, x4, x45, x6, x67])

    x89 = add_gate_with_TT(circuit, x8, x9, '0110')
    x1011 = add_gate_with_TT(circuit, x10, x11, '0110')
    w0, d1, d12 = add_mdfa(circuit, [c0, x8, x89, x10, x1011])

    w1, e2, e23 = add_mdfa(circuit, [a1, c1, c12, d1, d12])
    w3 = add_gate_with_TT(circuit, e2, e23, '0010')

    return w0, w1, e23, w3


def add_sum12_size41(circuit, input_labels):
    assert len(input_labels) == 12
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12 = input_labels

    a0, a1 = add_sum3(circuit, [x1, x2, x3])

    x45 = add_gate_with_TT(circuit, x4, x5, '0110')
    x67 = add_gate_with_TT(circuit, x6, x7, '0110')
    c0, c1, c12 = add_mdfa(circuit, [a0, x4, x45, x6, x67])

    x89 = add_gate_with_TT(circuit, x8, x9, '0110')
    x1011 = add_gate_with_TT(circuit, x10, x11, '0110')
    d0, d1, d12 = add_mdfa(circuit, [c0, x8, x89, x10, x1011])

    w0, e1 = add_sum2(circuit, [d0, x12])

    f1, f2, f23 = add_mdfa(circuit, [a1, c1, c12, d1, d12])
    w1, h2 = add_sum2(circuit, [e1, f1])

    w2, w3 = add_stockmeyer_block(circuit, [h2, f2, f23])

    return w0, w1, w2, w3


def add_sum13_size43(circuit, input_labels):
    assert len(input_labels) == 13
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13 = input_labels

    x67 = add_gate_with_TT(circuit, x6, x7, '0110')
    x89 = add_gate_with_TT(circuit, x8, x9, '0110')
    x1011 = add_gate_with_TT(circuit, x10, x11, '0110')
    x1213 = add_gate_with_TT(circuit, x12, x13, '0110')

    a0, a1, a2 = add_sum5_size11(circuit, [x1, x2, x3, x4, x5])
    b0, b1, b12 = add_mdfa(circuit, [a0, x6, x67, x8, x89])
    w0, c1, c12 = add_mdfa(circuit, [b0, x10, x1011, x12, x1213])
    w1, d2, d23 = add_mdfa(circuit, [a1, b1, b12, c1, c12])
    w2, w3 = add_stockmeyer_block(circuit, [a2, d2, d23])

    return w0, w1, w2, w3


def add_mdfa(circuit, input_labels):
    assert len(input_labels) == 5
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    z, x1, xy1, x2, xy2 = input_labels

    g1 = add_gate_with_TT(circuit, x1, z, '0110')
    g2 = add_gate_with_TT(circuit, xy1, g1, '0111')
    g3 = add_gate_with_TT(circuit, xy1, z, '0110')
    g4 = add_gate_with_TT(circuit, g2, g3, '0110')
    g5 = add_gate_with_TT(circuit, x2, g3, '0110')
    g6 = add_gate_with_TT(circuit, g3, xy2, '0110')
    g7 = add_gate_with_TT(circuit, g5, xy2, '0010')
    g8 = add_gate_with_TT(circuit, g2, g7, '0110')

    return g6, g4, g8


# an MDFA block with z=0
def add_simplified_mdfa(circuit, input_labels):
    assert len(input_labels) == 4
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, xy1, x2, xy2 = input_labels

    g2 = add_gate_with_TT(circuit, xy1, x1, '0111')
    g4 = add_gate_with_TT(circuit, g2, xy1, '0110')
    g5 = add_gate_with_TT(circuit, x2, xy1, '0110')
    g6 = add_gate_with_TT(circuit, xy1, xy2, '0110')
    g7 = add_gate_with_TT(circuit, g5, xy2, '0010')
    g8 = add_gate_with_TT(circuit, g2, g7, '0110')

    return g6, g4, g8


def add_sum14_size48(circuit, input_labels):
    assert len(input_labels) == 14
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15 = input_labels

    x45 = add_gate_with_TT(circuit, x4, x5, '0110')
    x67 = add_gate_with_TT(circuit, x6, x7, '0110')
    x89 = add_gate_with_TT(circuit, x8, x9, '0110')
    x1011 = add_gate_with_TT(circuit, x10, x11, '0110')
    x1213 = add_gate_with_TT(circuit, x12, x13, '0110')
    x1415 = add_gate_with_TT(circuit, x14, x15, '0110')

    a0, a1 = add_sum2(circuit, [x2, x3])
    b0, b1, b12 = add_mdfa(circuit, [a0, x4, x45, x6, x67])
    c0, c1, c12 = add_mdfa(circuit, [b0, x8, x89, x10, x1011])
    w0, d1, d12 = add_mdfa(circuit, [c0, x12, x1213, x14, x1415])
    e1, e2, e23 = add_mdfa(circuit, [a1, b1, b12, c1, c12])
    w1, f2 = add_stockmeyer_block(circuit, [e1, d1, d12])
    w2, w3 = add_stockmeyer_block(circuit, [f2, e2, e23])

    return w0, w1, w2, w3


def add_sum15_size51(circuit, input_labels):
    assert len(input_labels) == 15
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15 = input_labels

    x45 = add_gate_with_TT(circuit, x4, x5, '0110')
    x67 = add_gate_with_TT(circuit, x6, x7, '0110')
    x89 = add_gate_with_TT(circuit, x8, x9, '0110')
    x1011 = add_gate_with_TT(circuit, x10, x11, '0110')
    x1213 = add_gate_with_TT(circuit, x12, x13, '0110')
    x1415 = add_gate_with_TT(circuit, x14, x15, '0110')

    a0, a1 = add_sum3(circuit, [x1, x2, x3])
    b0, b1, b12 = add_mdfa(circuit, [a0, x4, x45, x6, x67])
    c0, c1, c12 = add_mdfa(circuit, [b0, x8, x89, x10, x1011])
    w0, d1, d12 = add_mdfa(circuit, [c0, x12, x1213, x14, x1415])
    e1, e2, e23 = add_mdfa(circuit, [a1, b1, b12, c1, c12])
    w1, f2 = add_stockmeyer_block(circuit, [e1, d1, d12])
    w2, w3 = add_stockmeyer_block(circuit, [f2, e2, e23])

    return w0, w1, w2, w3


def add_sum16_size59(circuit, input_labels):
    assert len(input_labels) == 16
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16 = input_labels

    q0, q1, q2, q3 = add_sum15_size51(circuit, input_labels[:-1])
    w0, a1 = add_sum2(circuit, [q0, x16])
    w1, b2 = add_sum2(circuit, [q1, a1])
    w2, c3 = add_sum2(circuit, [q2, b2])
    w3, w4 = add_sum2(circuit, [q3, c3])

    return w0, w1, w2, w3, w4


def add_sum31(circuit, input_labels):
    assert len(input_labels) == 31
    for input_label in input_labels:
        assert circuit.has_element(input_label)

    [x1, x2, x3, x4, x5, x6, x7, x8, x9, x10, x11, x12, x13, x14, x15, x16,
     x17, x18, x19, x20, x21, x22, x23, x24, x25, x26, x27, x28, x29, x30, x31] = input_labels

    a0, a1, a2 = add_sum7_size19(circuit, [x1, x2, x3, x4, x5, x6, x7])
    b0, b1, b2 = add_sum7_size19(circuit, [a0, x8, x9, x10, x11, x12, x13])
    c0, c1, c2 = add_sum7_size19(circuit, [b0, x14, x15, x16, x17, x18, x19])
    d0, d1, d2 = add_sum7_size19(circuit, [c0, x20, x21, x22, x23, x24, x25])
    w0, e1, e2 = add_sum7_size19(circuit, [d0, x26, x27, x28, x29, x30, x31])
    w1, f2, f3 = add_sum5_size11(circuit, [a1, b1, c1, d1, e1])
    g2, g3, g4 = add_sum5_size11(circuit, [a2, b2, c2, d2, e2])
    w2, h3 = add_sum2(circuit, [f2, g2])
    w3, i4 = add_sum3(circuit, [f3, g3, h3])
    w4 = f'z{len(circuit.gates)}'
    circuit.gates[w4] = (g4, i4, '0110')

    return w0, w1, w2, w3, w4


def check_sum_circuit(circuit):
    truth_tables = circuit.get_truth_table()
    n = len(circuit.inputs)

    for x in product(range(2), repeat=n):
        i = sum((2 ** (n - 1 - j)) * x[j] for j in range(n))
        s = sum(truth_tables[d][i] * (2 ** d) for d in range(len(circuit.outputs)))
        assert s == sum(
            x), f'Input: {x}, sum: {sum(x)}, s: {s}, output: {[truth_tables[d][i] for d in range(len(circuit.outputs))]}'


# computes the sum (2^w1)*x1+...+(2^wn)*xn
def add_sum_pow2_weights(circuit, weighted_inputs):
    weighted_bits, outputs = sorted(list(weighted_inputs)), []

    while weighted_bits:
        if len(weighted_bits) == 1 or weighted_bits[0][0] < weighted_bits[1][0]:
            outputs += [weighted_bits[0][1]]
            weighted_bits = weighted_bits[1:]
        elif len(weighted_bits) == 2:
            (w1, x1), (w2, x2) = weighted_bits[:2]
            if w1 < w2:
                outputs += [weighted_bits[0][1], weighted_bits[1][1]]
                weighted_bits = weighted_bits[2:]
            else:
                assert w1 == w2
                weighted_bits = weighted_bits[2:]
                s, c = add_sum2(circuit, [x1, x2])
                weighted_bits += [(w1, s), (w1 + 1, c)]
                weighted_bits = sorted(weighted_bits)
        else:
            (w1, x1), (w2, x2), (w3, x3) = weighted_bits[:3]
            if w1 == w2 == w3:
                weighted_bits = weighted_bits[3:]
                s, c = add_sum3(circuit, [x1, x2, x3])
                weighted_bits += [(w1, s), (w1 + 1, c)]
                weighted_bits = sorted(weighted_bits)
            elif w1 == w2:
                assert w3 > w2
                weighted_bits = weighted_bits[2:]
                s, c = add_sum2(circuit, [x1, x2])
                weighted_bits += [(w1, s), (w1 + 1, c)]
                weighted_bits = sorted(weighted_bits)

    return outputs


def add_sum(circuit, input_labels):
    n = len(input_labels)
    assert n > 0
    if n == 1:
        return [input_labels[0]]
    if n == 2:
        return add_sum2(circuit, input_labels)
    if n == 3:
        return add_sum3(circuit, input_labels)
    if n == 4:
        return add_sum4(circuit, input_labels)
    if n == 5:
        return add_sum5_size11(circuit, input_labels)
    if n == 6:
        return add_sum6_size16(circuit, input_labels)
    if n == 7:
        return add_sum7_size19(circuit, input_labels)
    if n == 8:
        return add_sum8_size25(circuit, input_labels)
    if n == 9:
        return add_sum9_size27(circuit, input_labels)
    if n == 10:
        return add_sum10_size31(circuit, input_labels)
    if n == 11:
        return add_sum11_size34(circuit, input_labels)
    if n == 12:
        return add_sum12_size41(circuit, input_labels)
    if n == 13:
        return add_sum13_size43(circuit, input_labels)
    if n == 14:
        return add_sum14_size48(circuit, input_labels)
    if n == 15:
        return add_sum15_size51(circuit, input_labels)
    if n == 16:
        return add_sum16_size59(circuit, input_labels)

    # synthesizing a circuit of size 5n out of full adders
    return add_sum_pow2_weights(circuit, [(0, x) for x in input_labels])


# computes the sum w1*x1+...+wn*xn
def add_weighted_sum(circuit, weights, input_labels):
    assert len(input_labels) == len(weights)
    assert all(isinstance(w, int) and w > 0 for w in weights)

    weighted_bits = []
    for w, x in zip(weights, input_labels):
        k = 0
        while w:
            if w % 2 == 1:
                weighted_bits.append((k, x))
            w, k = w // 2, k + 1

    return add_sum_pow2_weights(circuit, weighted_bits)

# divides the sum into blocks of size 2^n-1 
# will be replaced with calls of 4.5n sums generator
def add_sum_pow2_m1(circuit, input_labels):
    n = len(input_labels)
    assert n > 0

    if n == 1:
        return [input_labels[0]]

    out = []
    it = 0
    while (len(input_labels) > 2):
        for pw in range(5, 1, -1):
            i = 2 ** pw - 1 
            while len(input_labels) >= i:
                out.append(add_sum(circuit, input_labels[0: i]))
                input_labels = input_labels[i:]
                input_labels.append(out[it][0])
                it += 1 
    if(len(input_labels) == 2):
        out.append(add_sum2(circuit, input_labels[0: 2]))
        input_labels = input_labels[2:]
        input_labels.append(out[it][0])

    out = [list(filter(None, x)) for x in zip_longest(*out)]
    out[0] = [out[0][len(out[0])-1]] 
    return out


def circ_size(ckt):
    return ckt.elements_number - len(ckt.inputs)


if __name__ == '__main__':
    ckt = Circuit()
    n = 7
    input_labels = [f'x{i}' for i in range(n)]
    for i in range(n):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res = add_sum(ckt, input_labels)
    for i in res:
        ckt.mark_as_output(i)

    check_sum_circuit(ckt)

    print(circ_size(ckt))
    # print(ckt.get_truth_table())
