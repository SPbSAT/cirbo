import sys
from cirbo.core import Gate
from cirbo.core.circuit import Circuit, INPUT
from cirbo.synthesis.generation.arithmetics import add_mul_karatsuba
from cirbo.synthesis.generation.arithmetics.multiplication import add_simple_karatsuba, add_dadda_karatsuba, \
    add_mul_our_karatsuba
from cirbo.synthesis.generation.arithmetics.summation \
import add_sum_n_bits_easy, add_sum_n_bits, generate_add_weighted_bits_efficient, generate_add_weighted_bits_naive
sys.setrecursionlimit(150000)


# Misha TODO: there is some debug printing in generate_sum_weighted_bits_from_list -> DONE
# Misha TODO: rename generate_sum_weighted_bits_from_list to generate_add_weighted_bits_efficient -> DONE
# Misha TODO: add a method generate_add_weighted_bits_naive (that works via Full Adders and Half Adders) -> DONE (it works in AIG and XAIG also

for k in range(1000, 10001, 1000):

    bad_vector = [i for i in range(k)]
    for i in range(k):
        bad_vector.append(i)
    bad_vector.append(0)
    bad_vector.append(0)

    n = 2 * k + 2
    m = k + 2
    bad_vector.sort()
    ckt = generate_add_weighted_bits_efficient(bad_vector)

    sz = ckt.gates_number()
    print(sz)
    print((4.5 * n - sz) / m)
# exit(0)
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


n = 64
input_labels_a = [f"a{i}" for i in range(n)]
input_labels_b = [f"b{i}" for i in range(n)]
ckt_simple_karatsuba = Circuit()
ckt_dadda_karatsuba = Circuit()
ckt_pow2_m1_karatsuba = Circuit()
ckt_our_karatsuba = Circuit()


for i in input_labels_a:
    ckt_simple_karatsuba.add_gate(Gate(i, INPUT))
for i in input_labels_b:
    ckt_simple_karatsuba.add_gate(Gate(i, INPUT))

for i in input_labels_a:
    ckt_dadda_karatsuba.add_gate(Gate(i, INPUT))
for i in input_labels_b:
    ckt_dadda_karatsuba.add_gate(Gate(i, INPUT))

for i in input_labels_a:
    ckt_pow2_m1_karatsuba.add_gate(Gate(i, INPUT))
for i in input_labels_b:
    ckt_pow2_m1_karatsuba.add_gate(Gate(i, INPUT))

for i in input_labels_a:
    ckt_our_karatsuba.add_gate(Gate(i, INPUT))
for i in input_labels_b:
    ckt_our_karatsuba.add_gate(Gate(i, INPUT))

res = add_simple_karatsuba(ckt_simple_karatsuba, input_labels_a, input_labels_b)
ckt_simple_karatsuba.set_outputs(res)

res = add_dadda_karatsuba(ckt_dadda_karatsuba, input_labels_a, input_labels_b)
ckt_dadda_karatsuba.set_outputs(res)

res = add_mul_karatsuba(ckt_pow2_m1_karatsuba, input_labels_a, input_labels_b)
ckt_pow2_m1_karatsuba.set_outputs(res)

res = add_mul_our_karatsuba(ckt_our_karatsuba, input_labels_a, input_labels_b)
ckt_our_karatsuba.set_outputs(res)

print(f'Simple karatsuba circuit for multiplication of two {n}-bit numbers: {ckt_simple_karatsuba.gates_number()}')
print(f'Karatsuba with Dadda last step circuit for multiplication of two {n}-bit numbers: {ckt_dadda_karatsuba.gates_number()}')
print(f'Karatsuba with add_mul_pow2_m1 last step circuit for multiplication of two {n}-bit numbers: {ckt_pow2_m1_karatsuba.gates_number()}')
print(f'Karatsuba with our efficient summation circuit for multiplication of two {n}-bit numbers: {ckt_our_karatsuba.gates_number()}')