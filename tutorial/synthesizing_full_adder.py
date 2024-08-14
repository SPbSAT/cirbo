from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat
from boolean_circuit_tool.core.python_function import PyFunction


def sum_3(x1, x2, x3):
    s = x1 + x2 + x3
    return [(s >> i) & 1 for i in range(2)]

func = PyFunction.from_positional(sum_3)
circuit_finder = CircuitFinderSat(func, 5, basis='XAIG')
circuit = circuit_finder.find_circuit()
circuit.into_graphviz_digraph().view()
