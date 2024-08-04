import pytest
import random
from boolean_circuit_tool.core.boolean_function import BooleanFunction
from boolean_circuit_tool.core.circuit import Circuit, Gate
from boolean_circuit_tool.core.circuit.gate import Gate, INPUT
from boolean_circuit_tool.generation.arithmetics.add_mul import (
    add_mul,
    add_mul_alter,
    add_mul_dadda,
    add_mul_wallace,
    add_mul_pow2_m1,
    add_mul_karatsuba
)
from boolean_circuit_tool.generation.arithmetics.add_square import (
    add_square,
    add_square_pow2_m1
)

random.seed(42)

def to_bin(n, out_len):
    out = []
    for i in range(out_len):
        out.append(n%2)
        n /= 2
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
    if(len(inputs_a) == 1 or len(inputs_b) == 1):
        out_len -= 1

    return to_bin(a*b, out_len)

def test_mul():
    functions = [
        add_mul,
        add_mul_alter,
        add_mul_dadda,
        add_mul_wallace,
        add_mul_pow2_m1,
        add_mul_karatsuba
    ]
    sizes = [[1, 1], [1, 7], [7, 1], [3, 6], [8, 2], [64, 64]]
    for funct in functions:
        for [x, y] in sizes:
            ckt = Circuit()
            input_labels = [f'x{i}' for i in range(x+y)]
            for i in range(n):
                ckt.add_gate(Gate(input_labels[i], INPUT))

            res = funct(ckt, input_labels[:x], input_labels[x:])
            for i in res:
                ckt.mark_as_output(i)

            for test in range(1000):
                input_labels_a = [random.choice([0, 1]) for _ in range(x)]
                input_labels_b = [random.choice([0, 1]) for _ in range(y)]
                assert mul_naive(input_labels_a, input_labels_b) == ckt.evaluate(input_labels_a + input_labels_b)
            


