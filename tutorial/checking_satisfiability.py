import os 
import pathlib
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import is_circuit_satisfiable

path_circuit = str(pathlib.Path(os.path.dirname(__file__))) + '/../data/circuit.bench'
ckt = Circuit().from_bench_file(path_circuit)
if (sat_answer := is_circuit_satisfiable(ckt)).answer:
    print(sat_answer.model)
else:
    print("UNSATISFIABLE")
