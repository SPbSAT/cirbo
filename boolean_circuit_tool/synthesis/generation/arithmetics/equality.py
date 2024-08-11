import typing as tp

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.arithmetics._utils import (
    generate_random_label,
)

__all__ = [
    'add_equal',
]


def add_equal(circuit: Circuit, input_labels: tp.Sequence[str], num: int) -> str:
    """
    Compares the bit sequence represented by `input_labels` with the integer `num`.

    :param circuit: The circuit to which the comparison operation will be added.
    :param input_labels: A sequence of labels representing the bits to be compared.
    :param num: The integer value to compare against the bit sequence.
    :return: The label of the gate that represents the result of the comparison.

    """

    bits = bin(num)[2:].zfill(len(input_labels))[::-1]
    if len(bits) > len(input_labels):
        new_label = generate_random_label(circuit)
        circuit.add_gate(gate.Gate(new_label, gate.ALWAYS_FALSE))
        return new_label
    gates_for_and = []
    for i, (bit, inp) in enumerate(zip(bits, input_labels)):
        if bit == '0':
            new_label = generate_random_label(circuit)
            circuit.add_gate(gate.Gate(new_label, gate.NOT, (inp,)))
            gates_for_and.append(new_label)
        else:
            gates_for_and.append(inp)

    last_label = generate_random_label(circuit)
    if len(gates_for_and) == 1:
        return gates_for_and[0]
    circuit.add_gate(
        gate.Gate(last_label, gate.AND, (gates_for_and[0], gates_for_and[1]))
    )
    for i, (b, out) in enumerate(zip(bits[2:], gates_for_and[2:])):
        new_label = generate_random_label(circuit)
        circuit.add_gate(gate.Gate(new_label, gate.AND, (last_label, out)))
        last_label = new_label
    return last_label
