import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    reverse_if_big_endian,
)
from cirbo.synthesis.generation.arithmetics.div_mod import add_div_mod
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_constant

from cirbo.synthesis.generation.arithmetics.summation import add_sum_n_weighted_bits

from cirbo.synthesis.generation.helpers import GenerationBasis


def to_bin(circuit: Circuit, n: int):
    """
    Converts an integer constant to circuit labels representing its binary form.

    :param circuit: The general circuit.
    :param n: Integer constant to convert.
    :return: A list of gate labels representing the integer in little-endian format.

    """
    label = circuit.inputs[0]
    zero = add_gate_from_tt(
        circuit,
        label,
        label,
        '0000',
    )
    one = add_gate_from_tt(
        circuit,
        label,
        label,
        '1111',
    )
    res = []
    for i in range(n.bit_length()):
        if n & 1 << i:
            res.append(one)
        else:
            res.append(zero)
    return res


def extended_euclidean(a, b):
    """
    Calculates the greatest common divisor and Bezout coefficients.

    :param a: The first integer.
    :param b: The second integer.
    :return: A tuple ``(gcd, x, y)`` such that ``a * x + b * y == gcd``.

    """
    if b == 0:
        return a, 1, 0
    gcd, x, y = extended_euclidean(b, a % b)
    return gcd, y, x - (a // b) * y


def modular_inverse(M_i, m_i):
    """
    Calculates the modular inverse of ``M_i`` modulo ``m_i``.

    :param M_i: Integer value whose inverse should be found.
    :param m_i: Modulus for the inverse calculation.
    :return: The value ``x`` such that ``M_i * x == 1 mod m_i``.
    :raises ValueError: If the inverse does not exist.

    """
    gcd, x, _ = extended_euclidean(M_i, m_i)
    if gcd != 1:
        raise ValueError(f"Inverse does not exist for {M_i} mod {m_i}")
    return x % m_i


def _weighted_bits_to_labels(
    circuit: Circuit,
    weighted: list[tuple[int, gate.Label]],
) -> list[gate.Label]:
    """
    Converts weighted bit labels to a flat little-endian bit list.

    :param circuit: The general circuit.
    :param weighted: List of pairs where the first element is the bit power and the
        second element is the corresponding gate label.
    :return: A list of gate labels ordered by bit power in little-endian format.

    """
    if not weighted:
        return []
    max_power = max(p for p, _ in weighted)
    ref = weighted[0][1]
    zero = add_gate_from_tt(circuit, ref, ref, '0000')
    result: list[gate.Label] = [zero] * (max_power + 1)
    for power, label in weighted:
        result[power] = label
    return result


def add_crt(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduls: list[int],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Reconstructs a number from its residues using the Chinese Remainder Theorem.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing concatenated residues.
        For each modulus ``m``, the residue occupies ``(m - 1).bit_length()`` bits.
    :param moduls: List of pairwise coprime moduli.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A list of gate labels representing the reconstructed number modulo the
        product of all moduli.

    """
    input_labels_a = list(input_labels_a)

    if big_endian:
        input_labels_a.reverse()

    product = 1
    for mod in moduls:
        product *= mod
    M_i_list = [product // m for m in moduls]
    inverse_elements = [modular_inverse(M_i, m_i) for M_i, m_i in zip(M_i_list, moduls)]

    pointer = 0
    power_bits = []
    for i, mod in enumerate(moduls):
        bit_len = (mod - 1).bit_length()
        res = add_mul_constant(
            circuit,
            input_labels_a[pointer : pointer + bit_len],
            inverse_elements[i] * M_i_list[i],
            basis=basis,
        )
        for j in range(len(res)):
            power_bits.append((j, res[j]))
        pointer += bit_len

    weighted_sum = add_sum_n_weighted_bits(circuit, power_bits, basis=basis)
    sum_bits = _weighted_bits_to_labels(circuit, weighted_sum)
    product_bits = to_bin(circuit, product)
    _, ans = add_div_mod(circuit, sum_bits, product_bits)
    return reverse_if_big_endian(ans, big_endian)


def add_crt_calc(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduls: list[int],
    factors: list[int],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Reconstructs a number from its residues using predefined CRT factors.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing concatenated residues.
        For each modulus ``m``, the residue occupies ``(m - 1).bit_length()`` bits.
    :param moduls: List of moduli defining how to split the input labels.
    :param factors: Precomputed CRT factors. Each residue is multiplied by the factor
        with the same index, and the last element is used as the final modulus.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A list of gate labels representing the reconstructed number reduced by the
        final modulus from ``factors``.

    """
    input_labels_a = list(input_labels_a)

    if big_endian:
        input_labels_a.reverse()

    pointer = 0
    power_bits = []
    for i, mod in enumerate(moduls):
        bit_len = (mod - 1).bit_length()
        res = add_mul_constant(
            circuit,
            input_labels_a[pointer : pointer + bit_len],
            factors[i],
            basis=basis,
        )
        for j in range(len(res)):
            power_bits.append((j, res[j]))
        pointer += bit_len

    weighted_sum = add_sum_n_weighted_bits(circuit, power_bits, basis=basis)
    sum_bits = _weighted_bits_to_labels(circuit, weighted_sum)
    product_bits = to_bin(circuit, factors[-1])
    _, ans = add_div_mod(circuit, sum_bits, product_bits)
    return reverse_if_big_endian(ans, big_endian)
