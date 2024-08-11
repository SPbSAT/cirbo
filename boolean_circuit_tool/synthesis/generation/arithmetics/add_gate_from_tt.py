import random
import uuid

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    AND,
    Gate,
    GEQ,
    GT,
    LEQ,
    LIFF,
    LNOT,
    LT,
    NAND,
    NOR,
    NXOR,
    OR,
    RIFF,
    RNOT,
    XOR,
)

TT_to_type = {
    "0001": AND,
    "1011": GEQ,
    "0010": GT,
    "0000": ALWAYS_FALSE,
    "1101": LEQ,
    "0011": LIFF,
    "1100": LNOT,
    "0100": LT,
    "1110": NAND,
    "1000": NOR,
    "1111": ALWAYS_TRUE,
    "1001": NXOR,
    "0111": OR,
    "0101": RIFF,
    "1010": RNOT,
    "0110": XOR,
}


def get_new_label(circuit: Circuit) -> str:
    ans = "new_" + uuid.uuid4().hex
    while circuit.has_gate(ans):
        ans = "new_" + uuid.uuid4().hex
    return ans


def add_gate_with_TT(circuit: Circuit, label1: str, label2: str, operation: str) -> str:
    """
    Function add new gate with truth table format.

    :param circuit: The general circuit.
    :param label1: name of first gate.
    :param label2: name of second gate.
    :param operation: type of gate like TT format. In example '0101' or '0010'.
    :return: name of new gate.

    """
    label = get_new_label(circuit)
    circuit.add_gate(Gate(label, TT_to_type[operation], (label1, label2)))
    return label


__all__ = [
    "add_gate_with_TT",
]
