from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, NOR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics import add_mul
from boolean_circuit_tool.synthesis.generation.arithmetics import add_equal
from math import ceil, log2


def factorization(number: int) -> Circuit:
    n = ceil(math.log2(number + 1))
    ckt = Circuit.bare_circuit(input_size=2 * (n - 1))
    p, q = ckt.inputs[:n - 1], ckt.inputs[n - 1:]
    outs = add_mul(ckt, q, p)
    g3 = add_equal(ckt, outs, number)
    ckt.mark_as_output(g3)
    return ckt
