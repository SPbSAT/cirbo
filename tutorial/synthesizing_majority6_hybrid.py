from boolean_circuit_tool.core import DontCare, PyFunctionModel
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat
from boolean_circuit_tool.synthesis.generation.arithmetics import generate_sum_n_bits


def geq3(x: bool, y: bool, z: bool):
    s = x + 2 * y + 4 * z
    return [DontCare] if s > 6 else [True] if s >= 3 else [False]

ckt = generate_sum_n_bits(n=6)
pfm = PyFunctionModel.from_positional(geq3)
cfs = CircuitFinderSat(pfm, 2, basis='XAIG')
geq3_ckt = cfs.find_circuit()
ckt.extend_circuit(geq3_ckt, name='geq3')
ckt.view_graph()
