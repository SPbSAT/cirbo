from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat, Basis
from boolean_circuit_tool.core.python_function import PyFunction


def block(x: bool, y: bool, z: bool):
    s = x + 2 * y + 4 * z
    return [DontCare] if s > 6 else [True] if s >= 3 else [False]


ckt = Circuit()
ckt.add_inputs(['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
out = add_sum_n_bits(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
circuit_finder = CircuitFinderSat(PyFunction(block), number_of_gates=2, basis=Basis.XAIG)
new_block = circuit_finder.find_circuit()
ckt.connect_circuit(new_block, out, new_block.inputs)
