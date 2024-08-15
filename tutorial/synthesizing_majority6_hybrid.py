from boolean_circuit_tool.core import DontCare, PyFunction
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat
from boolean_circuit_tool.synthesis.generation.arithmetics import generate_sum_n_bits


def geq3_py(x: bool, y: bool, z: bool):
    s = x + 2 * y + 4 * z
    return [DontCare] if s > 6 else [True] if s >= 3 else [False]


ckt = generate_sum_n_bits(n=6)
func = PyFunction.from_positional(geq3_py)
finder = CircuitFinderSat(func, 2, basis='XAIG')
geq3 = finder.find_circuit()
ckt.extend_circuit(geq3,name='geq3')
ckt.view_graph()
