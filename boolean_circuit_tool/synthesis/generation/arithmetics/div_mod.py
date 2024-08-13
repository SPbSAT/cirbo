import typing as tp

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    validate_equal_sizes,
    validate_even,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.subtraction import (
    add_subtract_with_compare,
)


__all__ = [
    'add_div_mod',
    'generate_div_mod',
]


def generate_div_mod(inp_len: int, *, big_endian: bool = False) -> Circuit:
    """
    Generates a circuit that have div and mod two numbers (one number is first n bits,
    other is second n bits) in result.

    :param inp_len: number of input bits (must be even)
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: circuit that count div and mod.

    """

    validate_even(inp_len)
    circuit = Circuit.bare_circuit(inp_len)
    div, mod = add_div_mod(
        circuit,
        circuit.inputs[: (inp_len // 2)],
        circuit.inputs[(inp_len // 2) :],
        big_endian=big_endian,
    )
    circuit.set_outputs(div + mod)
    return circuit


def add_div_mod(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False
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

    # if we need result A % 0 = 0 and B / 0 = 0
    pref.append(add_gate_from_tt(circuit, pref[-1], b[0], "0111"))
    for i in range(n):
        result[i] = add_gate_from_tt(circuit, result[i], pref[-1], "0001")
    for i in range(n):
        now[i] = add_gate_from_tt(circuit, now[i], pref[-1], "0001")

    if big_endian:
        result.reverse()
        now.reverse()

    return result, now
