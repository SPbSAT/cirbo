import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
)

from cirbo.synthesis.generation.arithmetics.summation import add_sum_two_numbers, add_sum_n_weighted_bits
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_constant, add_mul_pow2_m1
from cirbo.synthesis.generation.arithmetics.div_mod import add_div_mod, add_div_predefined, add_mod_predefined

from cirbo.synthesis.generation.helpers import GenerationBasis

def to_bin(circuit: Circuit, n: int):
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
        if(n & 1 << i):
            res.append(one)
        else:
            res.append(zero)
    return res

def extended_euclidean(a, b):
    if b == 0:
        return a, 1, 0
    gcd, x, y = extended_euclidean(b, a % b)
    return gcd, y, x - (a // b) * y

def modular_inverse(M_i, m_i):
    gcd, x, _ = extended_euclidean(M_i, m_i)
    if gcd != 1:
        raise ValueError(f"Inverce does not exist for {M_i} mod {m_i}")
    return x % m_i

def add_crt(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduls: list[int],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    n = len(input_labels_a)
    m = len(moduls)

    if big_endian:
        input_labels_a.reverse()

    product = 1
    for mod in moduls:
        product *= mod
    M_i_list = [product // m for m in moduls]
    inverse_elements = [modular_inverse(M_i, m_i) for M_i, m_i in zip(M_i_list, moduls)]
    
    pointer = 0
    power_bits = []
    sum = []
    for i, mod in enumerate(moduls):
        l = (mod-1).bit_length()
        print(inverse_elements[i]*M_i_list[i])
        res = add_mul_constant(circuit, input_labels_a[pointer: pointer+l], inverse_elements[i]*M_i_list[i], basis=basis)
        for i in range(len(res)):
            power_bits.append((i, res[i])) 
        pointer += l

    sum = add_sum_n_weighted_bits(circuit, power_bits, basis=basis)
    product = to_bin(circuit, product)
    _, ans = add_div_mod(circuit, sum, product)
    return reverse_if_big_endian(ans)

def add_crt_calc(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    moduls: list[int],
    factors: list[int],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    input_labels_a = list(input_labels_a)
    n = len(input_labels_a)
    m = len(moduls)

    if big_endian:
        input_labels_a.reverse()
    
    pointer = 0
    power_bits = []
    for i, mod in enumerate(moduls):
        l = (mod-1).bit_length()
        print(factors[i])
        res = add_mul_constant(circuit, input_labels_a[pointer: pointer+l], factors[i], basis=basis)
        for i in range(len(res)):
            power_bits.append((i, res[i])) 
        pointer += l

    sum = add_sum_n_weighted_bits(circuit, power_bits, basis=basis)
    product = to_bin(circuit, factors[-1])
    _, ans = add_div_mod(circuit, sum, product)
    return ans