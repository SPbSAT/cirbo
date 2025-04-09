from cirbo.core.circuit import Circuit
from cirbo.synthesis.generation.arithmetics.summation \
    import add_sum_n_bits_easy, add_sum_n_bits, generate_add_weighted_bits_efficient, generate_add_weighted_bits_naive

# Misha TODO: there is some debug printing in generate_sum_weighted_bits_from_list -> DONE
# Misha TODO: rename generate_sum_weighted_bits_from_list to generate_add_weighted_bits_efficient -> DONE
# Misha TODO: add a method generate_add_weighted_bits_naive (that works via Full Adders and Half Adders) -> DONE (it works in AIG and XAIG also

n = 15

# Misha TODO: rewrite using generate_add_weighted_bits_naive -> DONE
ckt_sum_naive = generate_add_weighted_bits_naive([0] * n)
print(f'Naive circuit for SUM{n}: {ckt_sum_naive.gates_number()}')


ckt_sum_efficient = generate_add_weighted_bits_efficient([0] * n)
print(f'Efficient circuit for SUM{n}: {ckt_sum_efficient.gates_number()}')


ckt_add = generate_add_weighted_bits_efficient(list(range(n)) + list(range(n)))
print(f'(Optimal) addition of two {n}-bit numbers: {ckt_add.gates_number()}')


ckt_mult_efficient = generate_add_weighted_bits_efficient([i + j for i in range(n) for j in range(n)])
print(f'Efficient circuit for multiplication of two {n}-bit numbers: {ckt_mult_efficient.gates_number()}')

# Misha TODO: rewrite the following line using the new naive method -> DONE
ckt_mult_naive = generate_add_weighted_bits_naive([i + j for i in range(n) for j in range(n)])
print(f'Naive circuit for multiplication of two {n}-bit numbers: {ckt_mult_naive.gates_number()}')

