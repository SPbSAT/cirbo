import pathlib

from cirbo.circuits_db.data_utils import resolve_default_data_path
from cirbo.core.circuit import Circuit
from cirbo.sat import is_circuit_satisfiable


path = resolve_default_data_path(pathlib.Path('simple_circuit.bench'))
ckt = Circuit.from_bench_file(path)
print(ckt)

result = is_circuit_satisfiable(ckt)
print(result.answer)
