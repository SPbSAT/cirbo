from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import is_circuit_satisfiable


path_circuit = '../data/circuit.bench'
ckt = Circuit().from_bench_file(path_circuit)
result = is_circuit_satisfiable(ckt)
print(result.answer)
