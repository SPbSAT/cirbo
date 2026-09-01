"""
This tutorial demonstrates how to construct adders and compare two useful circuit
properties: the number of gates and the logical depth.  The first value in each table
cell is the gate count, and the second one is the depth (``gates/depth``).
"""

from cirbo.core.circuit import Circuit
from cirbo.synthesis.generation.arithmetics import (
    add_sum_two_numbers,
    add_sum_two_numbers_log_depth,
    add_sum_two_numbers_log_depth_brent_kung,
    add_sum_two_numbers_log_depth_krapchenko,
)


def make_adder(adder, width):
    circuit = Circuit.bare_circuit(2 * width)
    result = adder(
        circuit,
        circuit.inputs[:width],
        circuit.inputs[width:],
        # AIG makes the comparison fair: every implementation is generated using
        # the same gate basis.  String also can be used to set the basis.
        basis="AIG",
    )
    circuit.set_outputs(result)
    return circuit


# The ripple-carry adder has linear depth.  The other adders use prefix networks and
# reduce the depth to logarithmic, with different gate-count trade-offs.
adders = {
    "Ripple-carry": add_sum_two_numbers,
    "Kogge-Stone": add_sum_two_numbers_log_depth,
    "Brent-Kung": add_sum_two_numbers_log_depth_brent_kung,
    "Krapchenko": add_sum_two_numbers_log_depth_krapchenko,
}

# Each cell is number_of_gates / logical_depth.
print("name          n=4          n=8          n=16         n=32")
for name, adder in adders.items():
    values = []
    for width in (4, 8, 16, 32):
        # Rebuild the circuit for every width and calculate its parameters.
        circuit = make_adder(adder, width)
        size = circuit.gates_number()
        values.append(f"{size:3}/{circuit.get_depth():<2}")
    print(f"{name:12} " + "  ".join(values))
