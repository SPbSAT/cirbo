from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.synthesis.generation.arithmetics.add_n_bits_sum import (
    add_sub2,
    add_sub3,
)

__all__ = [
    'add_sub_with_per_equal_size',
]


def add_sub_with_per_equal_size(
    circuit: Circuit,
    input_labels_a: list[str],
    input_labels_b: list[str],
) -> (list[str], str):
    n = len(input_labels_a)
    assert n == len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_gate(input_label)
    for input_label in input_labels_b:
        assert circuit.has_gate(input_label)

    res = [0] * n
    bal = [0] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        res[i], bal[i] = add_sub3(
            circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]]
        )
    return res, bal[n - 1]
