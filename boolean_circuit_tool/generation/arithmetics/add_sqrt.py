from boolean_circuit_tool.generation.arithmetics.add_n_bits_sum import add_sub2, add_sub3, add_sum_two_numbers
from boolean_circuit_tool.generation.arithmetics.add_gate_from_TT import add_gate_with_TT
from boolean_circuit_tool.core.circuit import Circuit


def add_sub_with_per_equal_size(circuit: Circuit, input_labels_a: list[str], input_labels_b: list[str]) -> (
        list[str], str):
    n = len(input_labels_a)
    assert n == len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    res = [0] * n
    bal = [0] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        res[i], bal[i] = add_sub3(circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]])
    return res, bal[n - 1]


def add_sqrt(circuit: Circuit, input_labels: list[str]) -> list[str]:
    """
        Function find sqrt of integer.

        :param circuit: The general circuit.
        :param input_labels: the bits of the integer we want to find the sqrt for.
        """
    n = len(input_labels)
    half = n // 2
    for input_label in input_labels:
        assert circuit.has_element(input_label)
    x = input_labels.copy()
    ZERO = add_gate_with_TT(circuit, x[0], x[0], "0110")
    UNO = add_gate_with_TT(circuit, x[0], x[0], "1001")

    if n % 2 == 1:
        half += 1
        n += 1
        input_labels.append(ZERO)

    c = [ZERO for i in range(n)]
    for st in range(half - 1, -1, -1):
        sm = add_sum_two_numbers(circuit, c[(2 * st):], [UNO])
        sm = sm[:-1]
        sub_res, per = add_sub_with_per_equal_size(circuit, x[(2 * st):], sm)
        for i in range(st * 2, n):
            x[i] = add_gate_with_TT(circuit, add_gate_with_TT(circuit, per, sub_res[i - 2 * st], "0100"),
                                    add_gate_with_TT(circuit, x[i], per, "0001"), "0111")
        c = c[1:]
        c.append(ZERO)
        sm = add_sum_two_numbers(circuit, c[(2 * st):], [UNO])[:-1]
        for i in range(st * 2, n):
            c[i] = add_gate_with_TT(circuit, add_gate_with_TT(circuit, per, sm[i - 2 * st], "0100"),
                                    add_gate_with_TT(circuit, c[i], per, "0001"), "0111")
    return c[:half]


__all__ = [
    'add_sqrt',
]
