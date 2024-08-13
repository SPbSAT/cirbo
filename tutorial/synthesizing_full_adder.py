from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat, Basis
from boolean_circuit_tool.core.python_function import PyFunction


def sum_3(x1, x2, x3):
    s = x1 + x2 + x3
    return [(s >> i) & 1 for i in range(2)]


circuit_finder = CircuitFinderSat(PyFunction.from_positional(sum_3), number_of_gates=5, basis=Basis.XAIG)
circuit = circuit_finder.find_circuit()
circuit.into_graphviz_digraph().view()