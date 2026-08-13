import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    reverse_if_big_endian,
)
from cirbo.synthesis.generation.arithmetics.subtraction import add_subtract_with_compare
from cirbo.synthesis.generation.arithmetics.summation import (
    add_sum_two_numbers,
    xor_two_bits,
)
from cirbo.synthesis.generation.helpers import GenerationBasis


__all__ = [
    'add_sqrt',
    'generate_sqrt',
]


def generate_sqrt(
    inp_len: int,
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> Circuit:
    """
    Generates a circuit that have sqrt of number in result.

    :param inp_len: number of input bits (must be even)
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: A circuit whose outputs represent the integer square root of the input.

    """
    circuit = Circuit.bare_circuit(inp_len)
    res = add_sqrt(
        circuit,
        circuit.inputs,
        big_endian=big_endian,
        basis=basis,
    )
    circuit.set_outputs(res)
    return circuit


def add_sqrt(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Function find sqrt of integer.

    :param circuit: The general circuit.
    :param input_labels: the bits of the integer we want to find the sqrt for.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: the sqrt of integer.

    """
    input_labels = list(input_labels)
    n = len(input_labels)
    half = n // 2
    x = input_labels
    if big_endian:
        x.reverse()
    zero = xor_two_bits(circuit, x[0], x[0], basis=basis)

    if basis == GenerationBasis.XAIG:
        one = add_gate_from_tt(circuit, x[0], x[0], "1001")
    else:
        ab = add_gate_from_tt(circuit, x[0], x[0], '0001')
        nab = add_gate_from_tt(circuit, x[0], x[0], '1000')
        one = add_gate_from_tt(circuit, ab, nab, '0111')

    if n % 2 == 1:
        half += 1
        n += 1
        x.append(zero)

    c = [zero for _ in range(n)]
    for st in range(half - 1, -1, -1):
        sm = add_sum_two_numbers(circuit, c[(2 * st) :], [one], basis=basis)
        sm = sm[:-1]
        sub_res, per = add_subtract_with_compare(
            circuit, x[(2 * st) :], sm, basis=basis
        )
        for i in range(st * 2, n):
            x[i] = add_gate_from_tt(
                circuit,
                add_gate_from_tt(circuit, per, sub_res[i - 2 * st], "0100"),
                add_gate_from_tt(circuit, x[i], per, "0001"),
                "0111",
        )
        c = c[1:]
        c.append(zero)
        sm = add_sum_two_numbers(circuit, c[(2 * st) :], [one], basis=basis)[:-1]
        for i in range(st * 2, n):
            c[i] = add_gate_from_tt(
                circuit,
                add_gate_from_tt(circuit, per, sm[i - 2 * st], "0100"),
                add_gate_from_tt(circuit, c[i], per, "0001"),
                "0111",
            )
    return reverse_if_big_endian(c[:half], big_endian)
