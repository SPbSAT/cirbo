# Cirbo is a Python library that provides methods for
# Boolean circuit manipulations, analysis and synthesis.
# Code below demonstrates how simple Boolean circuit can
# be constructed, analyzed and drawn.
from cirbo.core import Circuit, Gate, gate
from cirbo.synthesis.generation.arithmetics import add_sum_n_bits

# Create an empty circuit with 6 inputs.
ckt = Circuit.bare_circuit(input_size=6)
# Generate and connect a "gadget" subcircuit
# that computes the sum of the input bits.
b0, b1, b2 = add_sum_n_bits(ckt, ckt.inputs)
# Manually add gates that yield True only
# if at least half of the inputs are True.
ckt.add_gate(Gate('a0', gate.AND, (b0, b1)))
ckt.add_gate(Gate('a1', gate.OR, ('a0', b2)))
ckt.mark_as_output('a1')

# Calculate general boolean function properties.
print(f"Is monotone: {ckt.is_monotone()}")
print(f"Is symmetric: {ckt.is_symmetric()}")
print(f"Is constant: {ckt.is_constant()}")

# Draw graph and show image in the default viewer.
ckt.view_graph()
