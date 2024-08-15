from boolean_circuit_tool.core import Circuit
from boolean_circuit_tool.minimization import minimize_subcircuits
from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum2, add_sum3


ckt = Circuit.bare_circuit(input_size=5)
x1, x2, x3, x4, x5 = ckt.inputs
a0, a1 = add_sum3(ckt, [x1, x2, x3])
b0, b1 = add_sum3(ckt, [a0, x4, x5])
w1, w2 = add_sum2(ckt, [a1, b1])
ckt.set_outputs([b0, w1, w2])
print(ckt.gates_number())
ckt = minimize_subcircuits(ckt, 'XAIG')
print(ckt.gates_number())
