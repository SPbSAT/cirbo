from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, NOR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics import add_mul
from boolean_circuit_tool.synthesis.generation.arithmetics import add_equal
from math import ceil, log2


def factorization(number: int) -> Circuit:
    n = ceil(log2(number))
    ckt = Circuit()
    xs1 = [f'x{i}' for i in range(n)]
    xs2 = [f'x{i}' for i in range(n, 2 * n)]
    ckt.add_inputs(xs1 + xs2)
    outs = add_mul(ckt, xs1, xs2)
    g1 = add_equal(ckt, xs1, 1)
    g2 = add_equal(ckt, xs2, 1)
    g3 = add_equal(ckt, outs, number)
    ckt.add_gate(Gate('g4', NOR, (g1, g2)))
    ckt.add_gate(Gate('g5', AND, ('g4', g3)))
    ckt.mark_as_output('g5')
    return ckt
