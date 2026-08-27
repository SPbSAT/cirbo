from cirbo.core.circuit import Circuit
from cirbo.minimization.simplification import RemoveRedundantGates
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
        basis="AIG",
    )
    circuit.set_outputs(result)
    return circuit


adders = {
    "Ripple-carry": add_sum_two_numbers,
    "Kogge-Stone": add_sum_two_numbers_log_depth,
    "Brent-Kung": add_sum_two_numbers_log_depth_brent_kung,
    "Krapchenko": add_sum_two_numbers_log_depth_krapchenko,
}

print("name          n=4          n=8          n=16         n=32")
for name, adder in adders.items():
    values = []
    for width in (4, 8, 16, 32):
        circuit = make_adder(adder, width)
        size = circuit.gates_number()
        values.append(f"{size:3}/{circuit.get_depth():<2}")
    print(f"{name:12} " + "  ".join(values))
