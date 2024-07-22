from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate
from boolean_circuit_tool.core.circuit.gate import (
    AND,
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
    ALWAYS_TRUE,
    ALWAYS_FALSE,
)
import random

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


def get_new_label(circuit: Circuit):
    ans = "new_" + str(random.randint(1, 1000000))
    while circuit.has_element(ans):
        ans = "new_" + str(random.randint(1, 100000000))
    return ans


def add_gate_with_TT(circuit, label1, label2, operation):
    label = get_new_label(circuit)
    circuit.add_gate(Gate(label, TT_to_type[operation], (label1, label2)))
    return label