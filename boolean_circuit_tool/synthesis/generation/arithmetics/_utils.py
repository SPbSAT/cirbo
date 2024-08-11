import uuid

from boolean_circuit_tool.core.circuit import Circuit, gate

from boolean_circuit_tool.synthesis.generation.exceptions import DifferentShapesError


__all__ = [
    'add_sub_with_per_equal_size',
    'generate_random_label',
    'add_gate_from_tt',
]


def add_sub_with_per_equal_size(
    circuit: Circuit,
    input_labels_a: list[gate.Label],
    input_labels_b: list[gate.Label],
) -> (list[gate.Label], gate.Label):
    """
    Subtracts given integer b from integer a and return complimentary bite representing
    if subtraction was successful (equivalent to a>=b).

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :return: label of

    """
    from boolean_circuit_tool.synthesis.generation.arithmetics.add_n_bits_sum import (
        add_sub2,
        add_sub3,
    )

    if len(input_labels_a) != len(input_labels_b):
        raise DifferentShapesError()

    n = len(input_labels_a)

    res = [0] * n
    bal = [0] * n

    res[0], bal[0] = add_sub2(
        circuit,
        [input_labels_a[0], input_labels_b[0]],
    )
    for i in range(1, n):
        res[i], bal[i] = add_sub3(
            circuit,
            [input_labels_a[i], input_labels_b[i], bal[i - 1]],
        )
    return res, bal[n - 1]


binary_tt_to_type = {
    "0001": gate.AND,
    "1011": gate.GEQ,
    "0010": gate.GT,
    "0000": gate.ALWAYS_FALSE,
    "1101": gate.LEQ,
    "0011": gate.LIFF,
    "1100": gate.LNOT,
    "0100": gate.LT,
    "1110": gate.NAND,
    "1000": gate.NOR,
    "1111": gate.ALWAYS_TRUE,
    "1001": gate.NXOR,
    "0111": gate.OR,
    "0101": gate.RIFF,
    "1010": gate.RNOT,
    "0110": gate.XOR,
}


def generate_random_label(circuit: Circuit) -> gate.Label:
    """
    Utility to generate random unoccupied name for new gate in `circuit`.

    :param circuit: Circuit to which new gate need to be added.
    :return: gate name, yet unoccupied in `circuit`.

    """
    _name = "new_" + uuid.uuid4().hex
    while circuit.has_gate(_name):
        _name = "new_" + uuid.uuid4().hex
    return _name


def add_gate_from_tt(
    circuit: Circuit,
    left: gate.Label,
    right: gate.Label,
    operation: str,
) -> gate.Label:
    """
    Function add new gate with truth table format.

    :param circuit: The general circuit.
    :param left: name of first gate.
    :param right: name of second gate.
    :param operation: type of gate given as a string truth table. For example, can be
        '0101' or '0010'.
    :return: label of new gate.

    """
    _label = generate_random_label(circuit)
    circuit.emplace_gate(
        label=_label,
        gate_type=binary_tt_to_type[operation],
        operands=(left, right),
    )
    return _label
