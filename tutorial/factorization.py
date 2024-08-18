from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import NOR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics import generate_mul, add_mul, generate_equal, add_equal
from math import ceil, log2


def factorization(number: int) -> Circuit:
    n = number.bit_length()
    ckt = Circuit.bare_circuit(input_size=2 * (n - 1))
    p, q = ckt.inputs[:n - 1], ckt.inputs[n - 1:]
    outs = add_mul(ckt, q, p)
    g3 = add_equal(ckt, outs, number)
    ckt.mark_as_output(g3)
    return ckt
