from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.minimization.subcircuit import minimize_subcircuits
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
from boolean_circuit_tool.synthesis.circuit_search import Basis

ckt = Circuit.bare_circuit(5)
x1, x2, x3, x4, x5 = ckt.inputs
a0, a1 = add_sum_n_bits(ckt, [x1, x2, x3])
b0, b1 = add_sum_n_bits(ckt, [a0, x4, x5])
w1, w2 = add_sum_n_bits(ckt, [a1, b1])
ckt.set_outputs([b0, w1, w2])
print(ckt.size)
minimize_subcircuits(ckt, basis=Basis.AIG)
print(ckt.size)