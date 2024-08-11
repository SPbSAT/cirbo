import math
import random

import pytest
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, INPUT
from boolean_circuit_tool.synthesis.generation.arithmetics.div_mod import add_div_mod
from boolean_circuit_tool.synthesis.generation.arithmetics.equality import add_equal
from boolean_circuit_tool.synthesis.generation.arithmetics.multiplication import (
    add_mul,
    add_mul_alter,
    add_mul_dadda,
    add_mul_karatsuba,
    add_mul_pow2_m1,
    add_mul_wallace,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.sqrt import add_sqrt
from boolean_circuit_tool.synthesis.generation.arithmetics.square import (
    add_square,
    add_square_pow2_m1,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import (
    add_sum_n_bits,
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
    return to_bin(a % b, len(inputs_b)) + to_bin(a // b, len(inputs_b))


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
def test_mul(func, size):
    x, y = size
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x + y)]
    for i in range(x + y):
        ckt.add_gate(Gate(input_labels[i], INPUT))

    res = func(ckt, input_labels[:x], input_labels[x:])
    for i in res:
        ckt.mark_as_output(i)

    for test in range(1000):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        input_labels_b = [random.choice([0, 1]) for _ in range(y)]
        assert (
            mul_naive(input_labels_a, input_labels_b)
            == ckt.evaluate(input_labels_a + input_labels_b)[::-1]
        )


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
def test_square(func, x):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x)]
    for i in range(x):
        ckt.add_gate(Gate(input_labels[i], INPUT))

    res = func(ckt, input_labels[:x])
    for i in res:
        ckt.mark_as_output(i)

    for test in range(1000):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        assert square_naive(input_labels_a) == ckt.evaluate(input_labels_a)[::-1]


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
def test_sqrt(x):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x)]
    for i in range(x):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res = add_sqrt(ckt, input_labels)
    for i in res:
        ckt.mark_as_output(i)
    for test in range(TEST_SIZE):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        assert sqrt_naive(input_labels_a) == ckt.evaluate(input_labels_a)[::-1]


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
def test_div_mod(x):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(2 * x)]
    for i in range(2 * x):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res_div, res_mod = add_div_mod(ckt, input_labels[:x], input_labels[x:])
    for i in res_div:
        ckt.mark_as_output(i)
    for i in res_mod:
        ckt.mark_as_output(i)
    for test in range(TEST_SIZE):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        input_labels_b = [random.choice([0, 1]) for _ in range(x)]
        if sum(input_labels_b) == 0:
            continue
        assert (
            div_mod_naive(input_labels_a, input_labels_b)
            == ckt.evaluate(input_labels_a + input_labels_b)[::-1]
        )


@pytest.mark.parametrize(
    "x",
    [
        2,
        5,
        7,
        17,
        60,
        128,
        pytest.param(1000, marks=pytest.mark.slow),
    ],
)
def test_sum_n_bits(x):
    ckt = Circuit()
    input_labels = [f'x{i}' for i in range(x)]
    for i in range(x):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res = add_sum_n_bits(ckt, input_labels)
    for i in res:
        ckt.mark_as_output(i)
    for test in range(TEST_SIZE):
        input_labels_a = [random.choice([0, 1]) for _ in range(x)]
        assert sum_naive(input_labels_a) == ckt.evaluate(input_labels_a)[::-1]
