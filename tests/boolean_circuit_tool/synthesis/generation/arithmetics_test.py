import math
import random

import pytest
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, INPUT
from boolean_circuit_tool.synthesis.generation import GenerationBasis
from boolean_circuit_tool.synthesis.generation.arithmetics import (
    add_div_mod,
    add_equal,
    add_mul,
    add_mul_alter,
    add_mul_dadda,
    add_mul_karatsuba,
    add_mul_pow2_m1,
    add_mul_wallace,
    add_sqrt,
    add_square,
    add_square_pow2_m1,
    add_sum_n_bits,
    generate_sum_n_bits,
)

TEST_SIZE = 100
random.seed(42)


def to_bin(n, out_len):
    out = []
    for i in range(out_len):
        out.append(n % 2)
        n //= 2
    return out[::-1]


def to_num(inputs):
    n = 0
    for i in inputs[::-1]:
        n *= 2
        n += i
    return n


def mul_naive(inputs_a, inputs_b):
    a = to_num(inputs_a)
    b = to_num(inputs_b)

    out_len = len(inputs_a) + len(inputs_b)
    if len(inputs_a) == 1 or len(inputs_b) == 1:
        out_len -= 1

    return to_bin(a * b, out_len)


def square_naive(inputs_a):
    a = to_num(inputs_a)

    out_len = 2 * len(inputs_a)
    if len(inputs_a) == 1:
        out_len -= 1

    return to_bin(a**2, out_len)


def sqrt_naive(inputs_a):
    a = to_num(inputs_a)
    out_len = (len(inputs_a) + 1) // 2
    return to_bin(int(a**0.5), out_len)


def div_mod_naive(inputs_a, inputs_b):
    a = to_num(inputs_a)
    b = to_num(inputs_b)
    return to_bin(a // b, len(inputs_b)) + to_bin(a % b, len(inputs_b))


def sum_naive(inputs_a):
    a = sum(inputs_a)
    len_res = int(math.log2(len(inputs_a))) + 1
    return to_bin(a, len_res)


@pytest.mark.parametrize(
    "func",
    [
        add_mul,
        add_mul_alter,
        add_mul_dadda,
        add_mul_wallace,
        add_mul_pow2_m1,
        add_mul_karatsuba,
    ],
)
@pytest.mark.parametrize(
    "size",
    [
        [1, 1],
        [1, 7],
        [7, 1],
        [3, 6],
        pytest.param([8, 2], marks=pytest.mark.slow),
        pytest.param([16, 16], marks=pytest.mark.slow),
        pytest.param([24, 15], marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_mul(func, size, big_endian):
    x, y = size
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x + y)]
    for i in range(x + y):
        ckt.add_gate(Gate(input_labels[i], INPUT))

    res = func(ckt, input_labels[:x], input_labels[x:], big_endian=big_endian)
    ckt.set_outputs(res)

    for test in range(TEST_SIZE):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        input_labels_b = [random.choice([0, 1]) for _ in range(y)]
        res = ckt.evaluate(input_labels_a + input_labels_b)
        if big_endian:
            input_labels_a.reverse()
            input_labels_b.reverse()
        else:
            res.reverse()

        assert mul_naive(input_labels_a, input_labels_b) == res


@pytest.mark.parametrize("func", [add_square, add_square_pow2_m1])
@pytest.mark.parametrize(
    "x",
    [
        1,
        2,
        5,
        7,
        pytest.param(17, marks=pytest.mark.slow),
        pytest.param(60, marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_square(func, x, big_endian):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x)]
    for i in range(x):
        ckt.add_gate(Gate(input_labels[i], INPUT))

    res = func(ckt, input_labels, big_endian=big_endian)
    ckt.set_outputs(res)

    for test in range(TEST_SIZE):
        input_labels = [random.choice([0, 1]) for _ in range(x)]
        res = ckt.evaluate(input_labels)
        if big_endian:
            input_labels.reverse()
        else:
            res.reverse()
        assert square_naive(input_labels) == res


@pytest.mark.parametrize("num", list(range(128)))
def test_add_equal(num):
    r = 7
    ckt = Circuit()
    inputs = [f"x{i}" for i in range(r)]
    for i in range(r):
        ckt.add_gate(Gate(inputs[i], INPUT))
    out_gate = add_equal(ckt, inputs, num)
    ckt.mark_as_output(out_gate)
    for i, b in enumerate(ckt.get_truth_table()[0]):
        if bin(i)[2:].zfill(r)[::-1] == bin(num)[2:].zfill(r):
            assert b
        else:
            assert not b


@pytest.mark.parametrize(
    "x",
    [
        2,
        4,
        9,
        pytest.param(21, marks=pytest.mark.slow),
        pytest.param(40, marks=pytest.mark.slow),
        pytest.param(64, marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_sqrt(x, big_endian):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x)]
    for i in range(x):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res = add_sqrt(ckt, input_labels, big_endian=big_endian)
    ckt.set_outputs(res)
    for test in range(TEST_SIZE):
        input_labels = [random.choice([0, 1]) for _ in range(x)]
        res = ckt.evaluate(input_labels)
        if big_endian:
            input_labels.reverse()
        else:
            res.reverse()
        assert sqrt_naive(input_labels) == res


@pytest.mark.parametrize(
    "x",
    [
        2,
        5,
        7,
        pytest.param(17, marks=pytest.mark.slow),
        pytest.param(60, marks=pytest.mark.slow),
        pytest.param(128, marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_div_mod(x, big_endian):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(2 * x)]
    for i in range(2 * x):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res_div, res_mod = add_div_mod(
        ckt, input_labels[:x], input_labels[x:], big_endian=big_endian
    )
    ckt.set_outputs(res_div + res_mod)
    for test in range(TEST_SIZE):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        input_labels_b = [random.choice([0, 1]) for _ in range(x)]
        if sum(input_labels_b) == 0:
            continue
        res = ckt.evaluate(input_labels_a + input_labels_b)
        if big_endian:
            input_labels_a.reverse()
            input_labels_b.reverse()
        else:
            res = res[:x][::-1] + res[x:][::-1]
        assert div_mod_naive(input_labels_a, input_labels_b) == res


@pytest.mark.parametrize("basis", [GenerationBasis.ALL, GenerationBasis.AIG])
@pytest.mark.parametrize(
    "n",
    list(range(1, 18))
    + [
        60,
        128,
        pytest.param(1000, marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_add_sum_n_bits(basis, n, big_endian):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(n)]
    for i in range(n):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res = add_sum_n_bits(ckt, input_labels, basis=basis, big_endian=big_endian)
    ckt.set_outputs(res)
    for test in range(TEST_SIZE):
        input_labels = [random.choice([0, 1]) for _ in range(n)]
        res = ckt.evaluate(input_labels)
        if not big_endian:
            res.reverse()
        assert sum_naive(input_labels) == res


@pytest.mark.parametrize("basis", [GenerationBasis.ALL, GenerationBasis.AIG])
@pytest.mark.parametrize(
    "n",
    list(range(1, 18))
    + [
        60,
        128,
        pytest.param(1000, marks=pytest.mark.slow),
    ],
)
@pytest.mark.parametrize("big_endian", [True, False])
def test_generate_sum_n_bits(basis, n, big_endian):
    ckt = generate_sum_n_bits(n, basis=basis, big_endian=big_endian)
    for test in range(TEST_SIZE):
        input_labels = [random.choice([0, 1]) for _ in range(n)]
        res = ckt.evaluate(input_labels)
        if not big_endian:
            res.reverse()
        assert sum_naive(input_labels) == res
