from cirbo.core import Circuit, Gate
from cirbo.minimization import cleanup

circ = Circuit.from_bench_file("../data/circuit.bench")
circ = cleanup(circ)