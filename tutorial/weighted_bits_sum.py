"""
Unlike ordinary summators, weighted-bit summators do not receive one bit-vector per
number.  Each input is paired with the power of two it contributes to, for example
``(3, x)`` means that ``x`` contributes ``x * 2**3`` to the result.

The example uses the columns of an 8-by-8 multiplication table.  The printed values
compare the gate count and logical depth of three implementations.
"""

from cirbo.core.circuit import Circuit
from cirbo.synthesis.generation.arithmetics import (
    add_sum_n_weighted_bits_log_depth,
    generate_sum_weighted_bits_efficient,
    generate_sum_weighted_bits_naive,
)


# ``shape[weight]`` is the number of input bits in a column with this weight.  This
# triangular shape is produced by the partial products of an 8-by-8 multiplication.
shape = [min(i, 16 - i) for i in range(1, 16)]

# The generators below accept a list of weights, while the log-depth implementation
# accepts explicit ``(weight, label)`` pairs.
weights = [weight for weight, count in enumerate(shape) for _ in range(count)]


def make_log_depth_summator():
    # A weighted input is not just a label: its first element identifies the binary
    # column in which the label belongs.  Several labels may have the same weight.
    circuit = Circuit.bare_circuit(len(weights))
    weighted_inputs = [
        (weight, circuit.inputs[index]) for index, weight in enumerate(weights)
    ]
    result = add_sum_n_weighted_bits_log_depth(circuit, weighted_inputs, basis="XAIG")
    # The result is returned as weighted ``(weight, label)`` pairs
    circuit.set_outputs([label for _, label in result])
    return circuit


summators = {
    # Efficient uses a linear-size construction, while Naive is a simple baseline.
    # Log-depth trades additional gates for a smaller logical depth.
    "Efficient": generate_sum_weighted_bits_efficient(weights, basis="XAIG"),
    "Log-depth": make_log_depth_summator(),
    "Naive": generate_sum_weighted_bits_naive(weights, basis="XAIG"),
}

for name, circuit in summators.items():
    print(f"{name:9} gates={circuit.gates_number():3}, depth={circuit.get_depth():2}")
