from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import is_circuit_satisfiable

ckt = Circuit().from_bench_file('../data/circuit.bench')
sat_answer = is_circuit_satisfiable(ckt)
if sat_answer.answer:
    print(sat_answer.model)
