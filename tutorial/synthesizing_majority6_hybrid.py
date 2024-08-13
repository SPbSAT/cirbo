from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat, Basis
from boolean_circuit_tool.core.python_function import PyFunction


def block(x: bool, y: bool, z: bool):
    s = x + 2 * y + 4 * z
    return [DontCare] if s > 6 else [True] if s >= 3 else [False]

ckt = Circuit().bare_circuit(6, prefix='x')
out = add_sum_n_bits(ckt, ckt.inputs)
circuit_finder = CircuitFinderSat(PyFunction.from_positional(block), number_of_gates=2, basis=Basis.XAIG)
new_block = circuit_finder.find_circuit()
ckt.connect_circuit(new_block, out, new_block.inputs, name='new_block', add_prefix=False)
ckt.into_graphviz_digraph().view()