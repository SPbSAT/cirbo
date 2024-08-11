import uuid

from boolean_circuit_tool.core.circuit import Circuit, gate


__all__ = [
    'binary_tt_to_type',
    'get_new_label',
    'add_gate_from_tt',
]


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


def get_new_label(circuit: Circuit) -> str:
    """
    Utility to generate random unoccupied name for new gate in `circuit`.

    :param circuit: Circuit to which new gate need to be added.
    :return: gate name, yet unoccupied in `circuit`.

    """
    _name = "new_" + uuid.uuid4().hex
    while circuit.has_gate(_name):
        _name = "new_" + uuid.uuid4().hex
    return _name


def add_gate_from_tt(circuit: Circuit, label1: str, label2: str, operation: str) -> str:
    """
    Function add new gate with truth table format.

    :param circuit: The general circuit.
    :param label1: name of first gate.
    :param label2: name of second gate.
    :param operation: type of gate given as a string truth table. In example '0101' or
        '0010'.
    :return: name of new gate.

    """
    label = get_new_label(circuit)
    circuit.add_gate(gate.Gate(label, binary_tt_to_type[operation], (label1, label2)))
    return label
