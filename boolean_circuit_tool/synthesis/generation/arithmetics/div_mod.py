from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    validate_equal_sizes,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.subtraction import (
    add_subtract_with_compare,
)


__all__ = [
    'add_div_mod',
]


def add_div_mod(
    circuit: Circuit,
    input_labels_a: list[str],
    input_labels_b: list[str],
) -> tuple[list[gate.Label], list[gate.Label]]:
    """
    Function make div two integers with equal size.

    :param circuit: The general circuit.
    :param input_labels_a: bits of divisible in increase order.
    :param input_labels_b: bits of divider in increase order.
    :return: first list is result for div, second list is result for mod.

    """
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

    return result, now
