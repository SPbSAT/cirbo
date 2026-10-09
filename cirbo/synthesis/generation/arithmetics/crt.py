import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    constant_to_bits,
    conventional_basis,
    reverse_if_big_endian,
)
from cirbo.synthesis.generation.arithmetics.div_mod import add_div_mod
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_constant
from cirbo.synthesis.generation.arithmetics.summation import add_sum_n_weighted_bits
from cirbo.synthesis.generation.exceptions import BadModulusError, BadShapesError
from cirbo.synthesis.generation.helpers import GenerationBasis

__all__ = [
    'add_crt',
    'add_crt_calc',
    'modular_inverse',
]


def modular_inverse(value: int, modulus: int) -> int:
    """
    Calculates the modular inverse of ``value`` modulo ``modulus``.

    :param value: Integer value whose inverse should be found.
    :param modulus: Modulus for the inverse calculation.
    :return: The value ``x`` such that ``value * x == 1 mod modulus``.
    :raises ValueError: If the inverse does not exist.

    """
    if value < 0:
        raise ValueError("Arguments must be non-negative")
    if modulus <= 0:
        raise BadModulusError("Modulus must be positive")
    try:
        return pow(value, -1, modulus)
    except ValueError as exc:
        raise ValueError(f"Inverse does not exist for {value} mod {modulus}") from exc


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
    max_power = max(power for power, _ in weighted)
    ref = weighted[0][1]
    zero = add_gate_from_tt(circuit, ref, ref, '0000')
    result = [zero] * (max_power + 1)
    for power, label in weighted:
        result[power] = label
    return result


def add_crt(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduli: list[int],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Reconstructs a number from its residues using the Chinese Remainder Theorem.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing concatenated residues.
        For each modulus ``m``, the residue occupies ``(m - 1).bit_length()`` bits.
    :param moduli: List of pairwise coprime moduli greater than one.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A list of gate labels representing the reconstructed number modulo the
        product of all moduli.

    """
    basis = conventional_basis(basis)
    product = 1
    for modulus in moduli:
        if modulus <= 1:
            raise BadModulusError("Moduli must be greater than one")
        product *= modulus

    product_parts = [product // modulus for modulus in moduli]
    inverse_elements = [
        modular_inverse(product_part, modulus)
        for product_part, modulus in zip(product_parts, moduli)
    ]
    factors = [
        inverse * product_part
        for inverse, product_part in zip(inverse_elements, product_parts)
    ]

    return add_crt_calc(
        circuit,
        input_labels_a,
        moduli,
        factors,
        product,
        big_endian=big_endian,
        basis=basis,
    )


def add_crt_calc(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduli: list[int],
    factors: list[int],
    final_modulus: int,
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Reconstructs a number from its residues using precomputed crt factors.

    :param circuit: The general circuit.
    :param input_labels_a: Iterable of gate labels representing concatenated residues.
        For each modulus ``m``, the residue occupies ``(m - 1).bit_length()`` bits.
    :param moduli: List of moduli greater than one defining how to split the input labels.
    :param factors: Precomputed crt factors. Each residue is multiplied by the factor
        with the same index.
    :param final_modulus: Positive modulus used to reduce the weighted sum.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A list of gate labels representing the reconstructed number reduced by the
        ``final_modulus``.

    """
    basis = conventional_basis(basis)
    if len(factors) != len(moduli):
        raise BadModulusError("Factors length must be equal to moduli length")
    if any(modulus <= 1 for modulus in moduli):
        raise BadModulusError("Moduli must be greater than one")
    if final_modulus <= 0:
        raise BadModulusError("Final modulus must be positive")

    input_labels_a = list(input_labels_a)
    expected_bits = sum((modulus - 1).bit_length() for modulus in moduli)
    if len(input_labels_a) != expected_bits:
        raise BadShapesError(
            f"Expected {expected_bits} input bits, got {len(input_labels_a)}"
        )
    pointer = 0
    power_bits = []
    for index, modulus in enumerate(moduli):
        bit_len = (modulus - 1).bit_length()
        residue = input_labels_a[pointer : pointer + bit_len]
        if big_endian:
            residue.reverse()
        res = add_mul_constant(
            circuit,
            residue,
            factors[index],
            basis=basis,
        )
        for power, label in enumerate(res):
            power_bits.append((power, label))
        pointer += bit_len

    weighted_sum = add_sum_n_weighted_bits(circuit, power_bits, basis=basis)
    sum_bits = _weighted_bits_to_labels(circuit, weighted_sum)
    product_bits = constant_to_bits(circuit, sum_bits[0], final_modulus)
    if len(sum_bits) < len(product_bits):
        zero = add_gate_from_tt(circuit, sum_bits[0], sum_bits[0], '0000')
        sum_bits.extend([zero] * (len(product_bits) - len(sum_bits)))
    _, ans = add_div_mod(circuit, sum_bits, product_bits, basis=basis)
    return reverse_if_big_endian(ans, big_endian)
