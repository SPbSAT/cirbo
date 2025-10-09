import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    validate_equal_sizes,
)
from cirbo.synthesis.generation.arithmetics.subtraction import add_subtract_with_compare, add_sub_two_numbers
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_karatsuba, add_mul_constant
from cirbo.synthesis.generation.arithmetics.summation import add_sum_two_numbers_with_shift
from cirbo.synthesis.generation.helpers import GenerationBasis

__all__ = [
    'add_div_mod',
    'add_div_predefined',
    'add_mod_predefined',
    'generate_div_mod',
]


def generate_div_mod(n: int, *, big_endian: bool = False) -> Circuit:
    """
    Generates a circuit that have div and mod two numbers (one number is first n bits,
    other is second n bits) in result.

    :param n: the number of bits in each number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: circuit that count div and mod.

    """

    circuit = Circuit.bare_circuit(2 * n)
    div, mod = add_div_mod(
        circuit,
        circuit.inputs[:n],
        circuit.inputs[n:],
        big_endian=big_endian,
    )
    circuit.set_outputs(div + mod)
    return circuit


def add_div_mod(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    zero_div: bool = False,
    big_endian: bool = False,
) -> tuple[list[gate.Label], list[gate.Label]]:
    """
    Function make div two integers with equal size.

    :param circuit: The general circuit.
    :param input_labels_a: bits of divisible in increase order.
    :param input_labels_b: bits of divider in increase order.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: first list is result for div, second list is result for mod.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    label = input_labels_a[0]
    zero = add_gate_from_tt(
        circuit,
        label,
        label,
        '0000',
    )
    extra = 0
    while(len(input_labels_b) < len(input_labels_a)):
        input_labels_b.append(zero)
        extra += 1
    validate_equal_sizes(input_labels_a, input_labels_b)

    n = len(input_labels_a)

    a = input_labels_a
    b = input_labels_b

    pref = [b[n - 1]]  # largest bit in b
    for i in range(n - 2, 0, -1):
        pref.append(
            add_gate_from_tt(
                circuit,
                pref[-1],
                b[i],
                "0111",
            )
        )

    result = [PLACEHOLDER_STR] * n
    now = a
    for i in range(n - 1, 0, -1):  # chose shift for sub (> 0)
        prov = pref[i - 1]
        m = n - i  # intersection
        sub_res, per = add_subtract_with_compare(circuit, now[(n - m) :], b[:m])
        result[i] = add_gate_from_tt(circuit, prov, per, "1000")
        for j in range(m):
            now[j + n - m] = add_gate_from_tt(
                circuit,
                add_gate_from_tt(circuit, result[i], sub_res[j], "0001"),
                add_gate_from_tt(circuit, now[j + n - m], result[i], "0010"),
                "0111",
            )

    m = n  # intersection
    sub_res, per = add_subtract_with_compare(circuit, now, b)
    result[0] = add_gate_from_tt(circuit, per, per, "1000")
    for j in range(m):
        now[j] = add_gate_from_tt(
            circuit,
            add_gate_from_tt(circuit, result[0], sub_res[j], "0001"),
            add_gate_from_tt(circuit, now[j], result[0], "0010"),
            "0111",
        )

    if zero_div: # if we need result A % 0 = 0 and B / 0 = 0
        pref.append(add_gate_from_tt(circuit, pref[-1], b[0], "0111"))
        for i in range(n):
            result[i] = add_gate_from_tt(circuit, result[i], pref[-1], "0001")
        for i in range(n):
            now[i] = add_gate_from_tt(circuit, now[i], pref[-1], "0001")
    
    else: # if we need result A % 0 = A and B / 0 = B
        pref.append(add_gate_from_tt(circuit, pref[-1], b[0], "0111"))
        and1 = [0 for i in range(n)]
        and2 = [0 for i in range(n)]
        for i in range(n):
            and1[i] = add_gate_from_tt(circuit, input_labels_a[i], pref[-1], "1000")
            and1[i] = add_gate_from_tt(circuit, and1[i], result[i], "0001")
            and2[i] = add_gate_from_tt(circuit, input_labels_a[i], pref[-1], "0010")
            and2[i] = add_gate_from_tt(circuit, and2[i], result[i], "0010")
            and1[i] = add_gate_from_tt(circuit, and1[i], and2[i], "0111")
        for i in range(n):
            result[i] = add_gate_from_tt(circuit, result[i], and1[i], "0110")
    

    if big_endian:
        result.reverse()
        now.reverse()

    return result, now[:n-extra]

def precompute_unsigned(N, d):
    if d == 0:
        raise ValueError("Divisor cannot be zero")

    l = d.bit_length() - 1
    shift = l

    if d == (1 << l):
        mul = 1
        add = 0
    else:
        big_one = 1 << (N + l)
        m_down = big_one // d
        m_up = m_down + 1
        temp = (m_up * d) & ((1 << N) - 1)

        if temp <= (1 << l):
            shift += N
            mul = m_up
            add = 0
        else:
            shift += N
            mul = m_down
            add = m_down

    return mul, add, shift  


def add_div_predefined(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    b: int,
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> tuple[list[gate.Label], list[gate.Label]]:
    input_labels_a = list(input_labels_a)
    if big_endian:
        input_labels_a.reverse()
    n = len(input_labels_a)
    if b == 0:
        raise ValueError("Division by zero")
    
    mul, add, shift = precompute_unsigned(n, b)

    out = add_mul_constant(circuit, input_labels_a, mul, basis=basis)
    if(add != 0):
        out = add_sum_two_numbers_with_shift(circuit, 0, out, (circuit, add))

    out = out[shift:]
    return out


def add_mod_predefined(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    b: int,
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    if big_endian:
        input_labels_a.reverse()
    n = len(input_labels_a)
    if b == 0:
        raise ValueError("Division by zero")
    
    div = add_div_predefined(circuit, input_labels_a, b, big_endian=big_endian, basis=basis)
    sub = add_mul_constant(circuit, div, b, basis=basis)
    res = add_sub_two_numbers(circuit, input_labels_a, sub)
    return res