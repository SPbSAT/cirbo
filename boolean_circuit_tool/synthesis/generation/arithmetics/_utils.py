import typing as tp
import uuid

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.synthesis.generation.exceptions import (
    BadShapesError,
    DifferentShapesError,
)


__all__ = [
    'PLACEHOLDER_STR',
    'add_gate_from_tt',
    'validate_const_size',
    'validate_equal_sizes',
    'validate_even',
    'generate_random_label',
    'generate_list_of_input_labels',
    'reverse_if_big_endian',
]


# String is a placeholder used in several generation methods
# to represent yet-to-be-filled gate Label in lists.
PLACEHOLDER_STR = '_PLACEHOLDER_STR_'


def validate_const_size(
    seq: tp.Sequence,
    sz: int,
):
    """Compares sequence size with const and raises if they are not equal."""
    if len(seq) != sz:
        raise DifferentShapesError(
            f"Labels sequence has bad length {len(seq)}, expected {sz}.",
        )


def validate_equal_sizes(
    seq_a: tp.Sequence,
    seq_b: tp.Sequence,
):
    """Compares provided sequences lengths and raises if they are not equal."""
    if len(seq_a) != len(seq_b):
        raise DifferentShapesError(
            f"Labels sequences have unequal lengths {len(seq_a)}!={len(seq_b)}.",
        )


def validate_even(size: int):
    """Raises BadShapesError if size (usually in generation) is not even."""
    if size % 2 != 0:
        raise BadShapesError("Generation size of this function must be even.")


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


def generate_list_of_input_labels(size: int) -> list[gate.Label]:
    """
    Utility to generate input labels for new circuit.

    :param size: number of inputs for we must choose a label.
    :return: list of gate names.

    """
    return [f'input{i}' for i in range(size)]


def reverse_if_big_endian(
    seq: tp.Iterable[gate.Label], big_endian: bool
) -> list[gate.Label]:
    res = list(seq)
    if big_endian:
        res.reverse()
    return res


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
