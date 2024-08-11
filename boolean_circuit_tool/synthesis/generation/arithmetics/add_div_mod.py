from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_sub_with_per_equal_size,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_gate_from_tt import (
    add_gate_with_TT,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_n_bits_sum import (
    add_sub2,
    add_sub3,
)

__all__ = []


def add_div_mod(
    circuit: Circuit, input_labels_a: list[str], input_labels_b: list[str]
) -> (list[str], list[str]):
    """
    Function make div two integers with equal size.

    :param circuit: The general circuit.
    :param input_labels_a: bits of divisible in increase order.
    :param input_labels_b: bits of divider in increase order.
    :return: first list is result for div, second list is result for mod.

    """
    n = len(input_labels_a)
    assert n == len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_gate(input_label)
    for input_label in input_labels_b:
        assert circuit.has_gate(input_label)

    a = input_labels_a
    b = input_labels_b
    pref = [b[n - 1]]  # larger bit in b
    for i in range(n - 2, 0, -1):
        pref.append(add_gate_with_TT(circuit, pref[-1], b[i], "0111"))
    result = [0] * n
    now = a
    for i in range(n - 1, 0, -1):  # chose shift for sub (> 0)
        prov = pref[i - 1]
        m = n - i  # intersection
        sub_res, per = add_sub_with_per_equal_size(circuit, now[(n - m) :], b[:m])
        result[i] = add_gate_with_TT(circuit, prov, per, "1000")
        for j in range(m):
            now[j + n - m] = add_gate_with_TT(
                circuit,
                add_gate_with_TT(circuit, result[i], sub_res[j], "0001"),
                add_gate_with_TT(circuit, now[j + n - m], result[i], "0010"),
                "0111",
            )
    m = n  # intersection
    sub_res, per = add_sub_with_per_equal_size(circuit, now, b)
    result[0] = add_gate_with_TT(circuit, per, per, "1000")
    for j in range(m):
        now[j] = add_gate_with_TT(
            circuit,
            add_gate_with_TT(circuit, result[0], sub_res[j], "0001"),
            add_gate_with_TT(circuit, now[j], result[0], "0010"),
            "0111",
        )

    # if we need result A % 0 = 0 and B / 0 = 0
    pref.append(add_gate_with_TT(circuit, pref[-1], b[0], "0111"))
    for i in range(n):
        result[i] = add_gate_with_TT(circuit, result[i], pref[-1], "0001")
    for i in range(n):
        now[i] = add_gate_with_TT(circuit, now[i], pref[-1], "0001")

    return result, now


__all__ = [
    'add_div_mod',
]
