from cirbo.synthesis.circuit_search import CircuitFinderSat
from cirbo.core.python_function import PyFunction


def sum_3(x1, x2, x3):
    s = x1 + x2 + x3
    return [(s >> i) & 1 for i in range(2)]

func = PyFunction.from_positional(sum_3)
cf = CircuitFinderSat(func, 5, basis='XAIG')
ckt = cf.find_circuit()
ckt.view_graph()
