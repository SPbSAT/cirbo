from cirbo.core.circuit import Circuit
from cirbo.sat import is_circuit_satisfiable


path = '../data/circuit.bench'
ckt = Circuit.from_bench_file(path)
result = is_circuit_satisfiable(ckt)
print(result.answer)
