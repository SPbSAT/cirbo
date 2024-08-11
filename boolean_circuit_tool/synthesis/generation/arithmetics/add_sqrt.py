from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    add_sub_with_per_equal_size,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_gate_from_tt import (
    add_gate_with_TT,
)
from boolean_circuit_tool.synthesis.generation.arithmetics.add_n_bits_sum import (
    add_sum_two_numbers,
)


def add_sqrt(circuit: Circuit, input_labels: list[str]) -> list[str]:
    """
    Function find sqrt of integer.

    :param circuit: The general circuit.
    :param input_labels: the bits of the integer we want to find the sqrt for.
    :return: the sqrt of integer.

    """
    n = len(input_labels)
    half = n // 2
    x = input_labels
    ZERO = add_gate_with_TT(circuit, x[0], x[0], "0110")
    UNO = add_gate_with_TT(circuit, x[0], x[0], "1001")

    if n % 2 == 1:
        half += 1
        n += 1
        x.append(ZERO)

    c = [ZERO for _ in range(n)]
    for st in range(half - 1, -1, -1):
        sm = add_sum_two_numbers(circuit, c[(2 * st) :], [UNO])
        sm = sm[:-1]
        sub_res, per = add_sub_with_per_equal_size(circuit, x[(2 * st) :], sm)
        for i in range(st * 2, n):
            x[i] = add_gate_with_TT(
                circuit,
                add_gate_with_TT(circuit, per, sub_res[i - 2 * st], "0100"),
                add_gate_with_TT(circuit, x[i], per, "0001"),
                "0111",
            )
        c = c[1:]
        c.append(ZERO)
        sm = add_sum_two_numbers(circuit, c[(2 * st) :], [UNO])[:-1]
        for i in range(st * 2, n):
            c[i] = add_gate_with_TT(
                circuit,
                add_gate_with_TT(circuit, per, sm[i - 2 * st], "0100"),
                add_gate_with_TT(circuit, c[i], per, "0001"),
                "0111",
            )
    return c[:half]


__all__ = [
    'add_sqrt',
]
