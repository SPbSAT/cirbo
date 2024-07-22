from boolean_circuit_tool.generation.arithmetics.add_n_bits_sum import (
    add_sum_two_numbers_with_shift,
    add_sum,
    add_sum_two_numbers,
    add_sub_two_numbers,
)
def add_mul(circuit, input_labels_a, input_labels_b):
    n = len(input_labels_a)
    m = len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    # in my mind a[0] is the smallest bit in a
    c = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            c[i][j] = circuit.add_gate(input_labels_a[j], input_labels_b[i], '0001')

    d = [[0] for _ in range(n + m)]
    d[0] = [c[0][0]]
    for i in range(1, n + m):
        inp = []
        for j in range(i + 1):
            if j < m and i - j < n:
                inp.append(c[j][i - j])
        for j in range(i):
            if j + len(d[j]) > i:
                inp.append(d[j][i - j])
        d[i] = add_sum(circuit, inp)
    return [d[i][0] for i in range(n + m)]


def add_mul_alter(circuit, input_labels_a, input_labels_b):
    n = len(input_labels_a)
    m = len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    # in my mind a[0] is the smallest bit in a
    c = [[0] * n for _ in range(m)]

    for i in range(m):
        for j in range(n):
            c[i][j] = circuit.add_gate(input_labels_a[j], input_labels_b[i], '0001')
    if m == 1:
        return [c[0]]

    res = add_sum_two_numbers_with_shift(circuit, 1, c[0], c[1])
    for i in range(2, m):
        res = add_sum_two_numbers_with_shift(circuit, i, res, c[i])

    return res


def add_mul_karatsuba(circuit, input_labels_a, input_labels_b):  # work on equal sizes
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    n = len(input_labels_a)
    if n < len(input_labels_b):
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
        n = len(input_labels_a)
    while n != len(input_labels_b):
        input_labels_b.append(circuit.add_gate(input_labels_a[0], input_labels_a[0], '0110'))

    if n < 16:
        return add_mul(circuit, input_labels_a, input_labels_b)

    mid = n // 2
    a = input_labels_a[mid:]
    b = input_labels_a[:mid]
    c = input_labels_b[mid:]
    d = input_labels_b[:mid]

    ac = add_mul_karatsuba(circuit, a, c)
    bd = add_mul_karatsuba(circuit, b, d)
    a_sum_b = add_sum_two_numbers(circuit, a, b)
    c_sum_d = add_sum_two_numbers(circuit, c, d)
    big_mul = add_mul_karatsuba(circuit, a_sum_b, c_sum_d)
    ac_sum_bd = add_sum_two_numbers(circuit, ac, bd)
    res_mid = add_sub_two_numbers(circuit, big_mul, ac_sum_bd)

    res = add_sum_two_numbers_with_shift(circuit, mid, bd, res_mid)
    final_res = add_sum_two_numbers_with_shift(circuit, n, res, ac)

    return final_res


def add_square(circuit, input_labels_a):
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    n = len(input_labels_a)

    if n < 10:
        return add_mul(circuit, input_labels_a, input_labels_a)

    mid = n // 2
    a = input_labels_a[mid:]
    b = input_labels_a[:mid]
    aa = add_square(circuit, a)
    bb = add_square(circuit, b)

    if n < 16:
        ab = add_mul(circuit, a, b)
    else:
        ab = add_mul_karatsuba(circuit, a, b)

    res = add_sum_two_numbers_with_shift(circuit, mid + 1, bb, ab)
    final_res = add_sum_two_numbers_with_shift(circuit, n, res, aa)[:-1]

    return final_res