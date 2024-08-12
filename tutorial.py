# Listing 1
import analysis as ans
import generation as gnt
import synthesis as snt
import minimizing as mnm

# Listing 2 (проверка по ветке py-function-extensions)

from boolean_circuit_tool.core.python_function import PyFunction
f = PyFunction(func=lambda xs: [sum(xs) %2], input_size=4)
# f.is_monotonic()
f.is_monotonic(inverse='False')
g = PyFunction.from_int_binary_func(2, 3,lambda x, y: x + y)
g.is_symmetric()


# Listing 3
from boolean_circuit_tool.core.circuit import Circuit, Gate, INPUT, AND
from boolean_circuit_tool.sat import is_circuit_satisfiable
circuit = Circuit()
circuit.add_gate(Gate('A', INPUT))
circuit.add_gate(Gate('B', INPUT))
circuit.add_gate(Gate('C', AND, ('A', 'B',),))
circuit.mark_as_output('C')
if(is_circuit_satisfiable(circuit).answer):
    is_circuit_satisfiable(circuit).model

# Или по старой версии 
ckt = Circuit().from_bench('circuit.bench')
if is_circuit_satisfiable(ckt).answer:
    print(is_circuit_satisfiable(ckt).model)


# Listing 4
# Видимо нужно дождаться add от Миши, но будет видимо что-то такое
x_sum = gnt.sum_n_bits(n=3, basis='xaig')
a_sum = gnt.sum_n_bits(n=3, basis='aig')
miter = ans.build_miter(x_sum, a_sum)
assert(not is_circuit_satisfiable(miter).answer)


# Listing 5
import math
from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, NOR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics.multiplication import add_mul
from boolean_circuit_tool.synthesis.generation.arithmetics.equality import add_equal
def factorization(number: int) -> Circuit:
    n_of_bits = int(math.log2(number))
    ckt = Circuit()
    xs1 = [f'x{i}' for i in range(n_of_bits)]
    xs2 = [f'x{i}' for i in range(n_of_bits, 2 * n_of_bits)]
    ckt.add_inputs(xs1 + xs2)
    outs = add_mul(ckt, xs1, xs2)
    g1 = add_equal(ckt, xs1, 1)
    g2 = add_equal(ckt, xs2, 1)
    g3 = add_equal(ckt, outs, number)
    ckt.add_gate(Gate("gate1", NOR, (g1, g2)))
    ckt.add_gate(Gate("gate2", AND, ("gate1", g3)))
    ckt.mark_as_output("gate2")
    return ckt


# Listing 6

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import Gate, OR, AND
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
ckt = Circuit()
ckt.add_inputs(['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
# b0, b1, b2 = add_sum(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
b0, b1, b2 = add_sum_n_bits(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
ckt.add_gate(Gate('a0', AND, (b0, b1)))
ckt.add_gate(Gate('a1', OR, ('a0', b2)))
ckt.mark_as_output('a1')


# Listing 7

from boolean_circuit_tool.synthesis.circuit_search import CircuitFinderSat, Basis
from boolean_circuit_tool.core.python_function import PyFunction
def sum_3(x1, x2, x3):
    s = x1 + x2 + x3
    return [(s >> i) & 1 for i in range(2)]

circuit_finder = CircuitFinderSat(PyFunction(sum_3), number_of_gates=5, basis=Basis.XAIG)
circuit = circuit_finder.find_circuit()


# Listing 8

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
# b0, b1, b2 = add_sum(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
out = add_sum_n_bits(ckt, ['x1', 'x2', 'x3', 'x4', 'x5', 'x6'])
circuit_finder = CircuitFinderSat(PyFunction(block), number_of_gates=2, basis=Basis.XAIG)
new_block = circuit_finder.find_circuit()
# ckt.connect_circuit([b0, b1, b2], new_block,new_block.inputs)
ckt.connect_circuit(new_block, out, new_block.inputs)


# Listing 9

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
ckt = Circuit(n=7)
# *, b2 = snt.add_sum(ckt, ckt.inputs)
*_, b2 = add_sum_n_bits(ckt, ckt.inputs)
# ckt.mark_output(b2)
ckt.mark_as_output(b2)
# Где найти такую функцию?
clean(ckt)


# Listing 10

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.minimization.subcircuit import minimize_subcircuits
from boolean_circuit_tool.synthesis.generation.arithmetics.summation import add_sum_n_bits
ckt = Circuit(n=5)
x1, x2, x3, x4, x5 = ckt.input_labels
a0, a1 = add_sum_n_bits(ckt, [x1, x2, x3])
b0, b1 = add_sum_n_bits(ckt, [a0, x4, x5])
w1, w2 = add_sum_n_bits(ckt, [a1, b1])
ckt.mark_outputs([b0, w1, w2])
# minimizing.minimize(ckt)
minimize_subcircuits(ckt)
