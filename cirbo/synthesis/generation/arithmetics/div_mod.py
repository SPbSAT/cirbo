import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    constant_to_bits,
    conventional_basis,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
    validate_equal_sizes,
    xor_two_bits,
)
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_constant
from cirbo.synthesis.generation.arithmetics.subtraction import (
    add_sub_two_numbers,
    add_subtract_with_compare,
)
from cirbo.synthesis.generation.arithmetics.summation import add_sum_two_numbers
from cirbo.synthesis.generation.exceptions import BadDivisorError
from cirbo.synthesis.generation.helpers import GenerationBasis

__all__ = [
    'add_div_mod',
    'add_div_mod_by_const',
    'generate_div_mod',
]


def generate_div_mod(
    n: int,
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> Circuit:
    """
    Generates a circuit that have div and mod two numbers (one number is first n bits,
    other is second n bits) in result.

    :param n: the number of bits in each number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: circuit that count div and mod.

    """

    basis = conventional_basis(basis)
    circuit = Circuit.bare_circuit(2 * n)
    div, mod = add_div_mod(
        circuit,
        circuit.inputs[:n],
        circuit.inputs[n:],
        big_endian=big_endian,
        basis=basis,
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
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> tuple[list[gate.Label], list[gate.Label]]:
    """
    Function make div two integers with equal size.

    :param circuit: The general circuit.
    :param input_labels_a: bits of divisible in increase order.
    :param input_labels_b: bits of divider in increase order.
    :param zero_div: if true, division by zero maps both quotient and remainder to zero;
        otherwise quotient and remainder are mapped to the dividend.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: first list is result for div, second list is result for mod.

    """
    basis = conventional_basis(basis)
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    extra = 0
    if len(input_labels_b) < len(input_labels_a):
        label = input_labels_a[0]
        zero = add_gate_from_tt(
            circuit,
            label,
            label,
            '0000',
        )
        extra = len(input_labels_a) - len(input_labels_b)
        input_labels_b.extend([zero] * extra)
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
        sub_res, per = add_subtract_with_compare(
            circuit, now[(n - m) :], b[:m], basis=basis
        )
        result[i] = add_gate_from_tt(circuit, prov, per, "1000")
        for j in range(m):
            now[j + n - m] = add_gate_from_tt(
                circuit,
                add_gate_from_tt(circuit, result[i], sub_res[j], "0001"),
                add_gate_from_tt(circuit, now[j + n - m], result[i], "0010"),
                "0111",
            )

    m = n  # intersection
    sub_res, per = add_subtract_with_compare(circuit, now, b, basis=basis)
    result[0] = add_gate_from_tt(circuit, per, per, "1000")
    for j in range(m):
        now[j] = add_gate_from_tt(
            circuit,
            add_gate_from_tt(circuit, result[0], sub_res[j], "0001"),
            add_gate_from_tt(circuit, now[j], result[0], "0010"),
            "0111",
        )

    if zero_div:  # if we need result A % 0 = 0 and B / 0 = 0
        pref.append(add_gate_from_tt(circuit, pref[-1], b[0], "0111"))
        for i in range(n):
            result[i] = add_gate_from_tt(circuit, result[i], pref[-1], "0001")
        for i in range(n):
            now[i] = add_gate_from_tt(circuit, now[i], pref[-1], "0001")

    else:  # if we need result A % 0 = A and B / 0 = B
        pref.append(add_gate_from_tt(circuit, pref[-1], b[0], "0111"))
        and1 = ["0" for i in range(n)]
        and2 = ["0" for i in range(n)]
        for i in range(n):
            and1[i] = add_gate_from_tt(circuit, input_labels_a[i], pref[-1], "1000")
            and1[i] = add_gate_from_tt(circuit, and1[i], result[i], "0001")
            and2[i] = add_gate_from_tt(circuit, input_labels_a[i], pref[-1], "0010")
            and2[i] = add_gate_from_tt(circuit, and2[i], result[i], "0010")
            and1[i] = add_gate_from_tt(circuit, and1[i], and2[i], "0111")
        for i in range(n):
            result[i] = xor_two_bits(circuit, result[i], and1[i], basis=basis)

    mod = now[: n - extra]
    return (
        reverse_if_big_endian(result, big_endian),
        reverse_if_big_endian(mod, big_endian),
    )


def _precompute_unsigned(n: int, d: int) -> tuple[int, int, int]:
    """
    Precompute multiplier constants for unsigned division by a fixed divisor.

    :param n: Width of the dividend.
    :param d: Non-zero divisor.
    :return: A tuple of multiplier, additive correction, and output shift.

    """
    if d <= 0:
        raise BadDivisorError("Divisor must be positive")

    length = d.bit_length() - 1
    shift = length

    if d == (1 << length):
        mul = 1
        add = 0
    else:
        big_one = 1 << (n + length)
        m_down = big_one // d
        m_up = m_down + 1
        temp = (m_up * d) & ((1 << n) - 1)

        if temp <= (1 << length):
            shift += n
            mul = m_up
            add = 0
        else:
            shift += n
            mul = m_down
            add = m_down

    return mul, add, shift


def add_div_mod_by_const(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    b: int,
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> tuple[list[gate.Label], list[gate.Label]]:
    """
    Divides an unsigned number by a non-zero integer constant and computes remainder.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing the dividend.
    :param b: Non-zero integer divisor.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: first list is result for div, second list is result for mod.

    """
    basis = conventional_basis(basis)
    input_labels_a = list(input_labels_a)
    if big_endian:
        input_labels_a.reverse()
    if b <= 0:
        raise BadDivisorError("Divisor must be positive")

    n = len(input_labels_a)
    mul, add_val, shift = _precompute_unsigned(n, b)

    div = add_mul_constant(circuit, input_labels_a, mul, basis=basis)
    if add_val != 0:
        add_bits = constant_to_bits(circuit, div[0], add_val)
        div = add_sum_two_numbers(circuit, div, add_bits, basis=basis)

    div = div[shift:]
    if div:
        sub = add_mul_constant(circuit, div, b, basis=basis)
        mod = add_sub_two_numbers(circuit, input_labels_a, sub, basis=basis)
    else:
        mod = input_labels_a
    return (
        reverse_if_big_endian(div, big_endian),
        reverse_if_big_endian(mod, big_endian),
    )
