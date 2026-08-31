from cirbo.core.circuit import Circuit
from cirbo.synthesis.generation.arithmetics import (
    add_sum_n_weighted_bits_log_depth,
    generate_sum_weighted_bits_efficient,
    generate_sum_weighted_bits_naive,
)


# The shape describes the number of bits in each weighted column of an 8-by-8 multiplication table
shape = [min(i, 16 - i) for i in range(1, 16)]
weights = [weight for weight, count in enumerate(shape) for _ in range(count)]


def make_log_depth_summator():
    circuit = Circuit.bare_circuit(len(weights))
    weighted_inputs = [
        (weight, circuit.inputs[index]) for index, weight in enumerate(weights)
    ]
    result = add_sum_n_weighted_bits_log_depth(circuit, weighted_inputs, basis="XAIG")
    circuit.set_outputs([label for _, label in result])
    return circuit


summators = {
    "Efficient": generate_sum_weighted_bits_efficient(weights, basis="XAIG"),
    "Log-depth": make_log_depth_summator(),
    "Naive": generate_sum_weighted_bits_naive(weights, basis="XAIG"),
}

for name, circuit in summators.items():
    print(f"{name:9} gates={circuit.gates_number():3}, depth={circuit.get_depth():2}")
