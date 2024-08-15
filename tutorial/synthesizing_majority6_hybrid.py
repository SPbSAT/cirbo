from boolean_circuit_tool.core import Circuit, DontCare, PyFunction
from boolean_circuit_tool.synthesis.generation.arithmetics import add_sum_n_bits
from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat


def block(x: bool, y: bool, z: bool):
    s = x + 2 * y + 4 * z
    return [DontCare] if s > 6 else [True] if s >= 3 else [False]

ckt = Circuit.bare_circuit(input_size=6)
out = add_sum_n_bits(ckt, ckt.inputs)
func = PyFunction.from_positional(block)
finder = CircuitFinderSat(func, 2, basis='XAIG')
new_block = finder.find_circuit()
ckt.connect_circuit(new_block, out, new_block.inputs, name='new_block', add_prefix=False)
ckt.view_graph()
