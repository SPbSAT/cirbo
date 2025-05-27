import cirbo.synthesis.generation.arithmetics
import cirbo.core
from cirbo.core import Circuit, Gate
from cirbo.core.circuit import INPUT
from cirbo.core.circuit.operators import always_false_
from cirbo.minimization import RemoveRedundantGates
from cirbo.synthesis.generation.arithmetics import add_sqrt, add_sum_two_numbers, add_subtract_with_compare, \
    add_sub_two_numbers
from cirbo.synthesis.generation.arithmetics._utils import add_gate_from_tt, PLACEHOLDER_STR
from cirbo.synthesis.generation.arithmetics.square import add_square


ckt = Circuit()
n = 8
total_len = n
a = [f'a{i}' for i in range(n)]
b = [f'b{i}' for i in range(n)]
for i in range(n):
    ckt.add_gate(Gate(a[i], INPUT))
for i in range(n):
    ckt.add_gate(Gate(b[i], INPUT))

always_false = add_gate_from_tt(ckt, a[0], a[0], "0000")
always_true = add_gate_from_tt(ckt, a[0], a[0], "1111")

def get_list_from_num(x): # from small to big bits
    global always_true, always_false
    gates = []
    st = 2 ** 7
    while st > 0:
        if x >= st:
            gates.append(always_true)
            x -= st
        else:
            gates.append(always_false)
        st //= 2
    gates.reverse()
    return gates


gates_32 = get_list_from_num(32)
gates_64 = get_list_from_num(64)
gates_96 = get_list_from_num(96)
gates_128 = get_list_from_num(128)
gates_129 = get_list_from_num(129)
gates_192 = get_list_from_num(192)
gates_224 = get_list_from_num(224)

def if_flag_from_two_options(
    circuit: Circuit,
    input_labels_a,
    input_labels_b,
    flag
): # if flag => a, if !flag => b
    result = [PLACEHOLDER_STR] * total_len
    for i in range(total_len):
        result[i] = add_gate_from_tt(circuit, input_labels_a[i], flag, "0001")
        some_gate = add_gate_from_tt(circuit, input_labels_b[i], flag, "0010")
        result[i] = add_gate_from_tt(circuit, result[i], some_gate, "0111")
    return result


def min_from_two_numbers(
    circuit: Circuit,
    input_labels_a,
    input_labels_b
):
    sub, bal = add_subtract_with_compare(circuit, input_labels_a, input_labels_b)
    return if_flag_from_two_options(circuit, input_labels_a, input_labels_b, bal)

def max_for_min(
circuit: Circuit,
    input_labels_a,
    input_labels_b,
    min_result
):
    max_result = [PLACEHOLDER_STR] * total_len
    for i in range(total_len):
        max_result[i] = add_gate_from_tt(circuit, input_labels_a[i], min_result[i], "0110")
        max_result[i] = add_gate_from_tt(circuit, input_labels_b[i], max_result[i], "0110")
    return max_result

def mul_on_2(input_labels_a):
    result = [PLACEHOLDER_STR] * (len(input_labels_a) + 1)
    for i in range(len(input_labels_a)):
        result[i + 1] = input_labels_a[i]
    result[0] = always_false
    return result

def div_on_2(input_labels_a):
    result = [always_false] * max(total_len, len(input_labels_a) - 1)
    for i in range(len(input_labels_a) -  1):
        result[i] = input_labels_a[i + 1]
    return result

m = min_from_two_numbers(ckt, a, b)
M = max_for_min(ckt, a, b, m)
result = [always_false] * total_len

_, M_at_least_224 = add_subtract_with_compare(ckt, M, gates_224)
_, M_at_least_192 = add_subtract_with_compare(ckt, M, gates_192)
_, M_at_least_128 = add_subtract_with_compare(ckt, M, gates_128)
_, M_at_least_64 = add_subtract_with_compare(ckt, M, gates_64)

_, m_at_least_192 = add_subtract_with_compare(ckt, m, gates_192)
_, m_at_least_96 = add_subtract_with_compare(ckt, m, gates_96)
_, m_at_least_128 = add_subtract_with_compare(ckt, m, gates_128)
_, m_at_least_64 = add_subtract_with_compare(ckt, m, gates_64)

M_from_224 = M_at_least_224
M_from_192_to_224 = add_gate_from_tt(ckt, M_at_least_192, M_at_least_224, "0010")
M_from_128_to_224 = add_gate_from_tt(ckt, M_at_least_128, M_at_least_224, "0010")
M_from_128_to_192 = add_gate_from_tt(ckt, M_at_least_128, M_at_least_192, "0010")
M_from_64_to_128 = add_gate_from_tt(ckt, M_at_least_64, M_at_least_128, "0010")
M_to_64 = add_gate_from_tt(ckt, M_at_least_64, M_at_least_64, "1000")

m_from_192 = m_at_least_192
m_from_128_to_192 = add_gate_from_tt(ckt, m_at_least_128, m_at_least_192, "0010")
m_from_96_to_128 = add_gate_from_tt(ckt, m_at_least_96, m_at_least_128, "0010")
m_from_64_to_96 = add_gate_from_tt(ckt, m_at_least_64, m_at_least_96, "0010")
m_to_64 = add_gate_from_tt(ckt, m_at_least_64, m_at_least_64, "1000")

res = gates_224

# now we need calculate all
# min(2 * M - m - 192, M - m // 2)
sum_m_M = add_sum_two_numbers(ckt, m, M)
sub_M_m= add_sub_two_numbers(ckt, M, m)
_, sub_m_M_at_least_129 = add_subtract_with_compare(ckt, sub_M_m, gates_129)
m_plus_1 = add_sum_two_numbers(ckt, m, [always_true])
sum_m_M_plus_1 = add_sum_two_numbers(ckt, m_plus_1, M)
sum_m_M_plus_1_div_2 = div_on_2(sum_m_M_plus_1)
sub_128_and_sub_M_m = add_sub_two_numbers(ckt, gates_128, sub_M_m)
m_mul_2 = mul_on_2(m)
M_mul_2 = mul_on_2(M)
M_mul_2_sub_m = add_sub_two_numbers(ckt, M_mul_2, m)
M_mul_2_sub_m_sub_192 = add_sub_two_numbers(ckt, M_mul_2_sub_m, gates_192)
div_m_2 = div_on_2(m)
M_sub_m_div_2 = add_sub_two_numbers(ckt, M, div_m_2)

res_min_in_45_line = min_from_two_numbers(ckt, M_sub_m_div_2, M_mul_2_sub_m_sub_192)

M_sub_m_sub_64 = add_sub_two_numbers(ckt, sub_M_m, gates_64)
M_sub_m_sub_64_mul_2 = mul_on_2(M_sub_m_sub_64)
sub_128_sub_M_m = add_sub_two_numbers(ckt, gates_128, sub_M_m)
sub_128_sub_M_m_mul_2 = mul_on_2(sub_128_and_sub_M_m)

sum_2m_and_64 = add_sum_two_numbers(ckt, m_mul_2, gates_64)
sum_2m_and_64_sub_M = add_sub_two_numbers(ckt, sum_2m_and_64, M)
M_div_2 = div_on_2(M)
sum_m_64 = add_sum_two_numbers(ckt, gates_64, m)
sum_m_64_sub_M_div_2 = add_sub_two_numbers(ckt, sum_m_64, M_div_2)

result_for_some_min_line_56 = min_from_two_numbers(ckt, sum_m_64_sub_M_div_2, sum_2m_and_64_sub_M)

_, is_sub_M_m_at_least_128 = add_subtract_with_compare(ckt, sub_M_m, gates_128)
sum_m_M_sub_128 = add_sub_two_numbers(ckt, sum_m_M, gates_128)
sum_m_M_plus_1_div_2_sum_32 = add_sum_two_numbers(ckt, sum_m_M_plus_1_div_2, gates_32)

res_of_min_in_63_line = min_from_two_numbers(ckt, sum_m_M_plus_1_div_2_sum_32, sum_m_M_sub_128)

m_plus_1_div_2 = div_on_2(m_plus_1)
m_plus_1_div_2_sum_M = add_sum_two_numbers(ckt, m_plus_1_div_2, M)
res_min_in_line_67 = min_from_two_numbers(ckt, gates_96, m_plus_1_div_2_sum_M)
res_min_in_line_69 = min_from_two_numbers(ckt, sum_m_M_plus_1_div_2_sum_32, sum_m_M)
m_plus_1_div_2_sum_M_sub_64 = add_sub_two_numbers(ckt, m_plus_1_div_2_sum_M, gates_64)
res_min_line_71 = min_from_two_numbers(ckt, gates_224, m_plus_1_div_2_sum_M_sub_64)

res = if_flag_from_two_options(ckt, res_min_in_45_line, res, add_gate_from_tt(ckt, M_from_192_to_224, m_to_64, "0001"))
inside_46 = if_flag_from_two_options(ckt, M_sub_m_sub_64_mul_2, sub_128_sub_M_m_mul_2, sub_m_M_at_least_129) ## need to think
res = if_flag_from_two_options(ckt, inside_46, res, add_gate_from_tt(ckt, M_from_192_to_224, m_from_64_to_96, "0001"))
res = if_flag_from_two_options(ckt, gates_96, res, add_gate_from_tt(ckt, M_from_192_to_224, m_from_96_to_128, "0001"))
res = if_flag_from_two_options(ckt, gates_96, res, add_gate_from_tt(ckt, M_from_128_to_192, m_from_96_to_128, "0001"))
res = if_flag_from_two_options(ckt, gates_96, res, add_gate_from_tt(ckt, M_from_128_to_224, m_from_96_to_128, "0001"))
res = if_flag_from_two_options(ckt, result_for_some_min_line_56, res, add_gate_from_tt(ckt, M_from_128_to_192, m_from_64_to_96, "0001"))
inside_57 = if_flag_from_two_options(ckt, sum_m_M, sub_128_sub_M_m, sub_m_M_at_least_129) ## need to think
res = if_flag_from_two_options(ckt, inside_57, res, add_gate_from_tt(ckt, M_from_128_to_192, m_from_128_to_192, "0001"))
res = if_flag_from_two_options(ckt, res_of_min_in_63_line, res, add_gate_from_tt(ckt, M_at_least_128, m_at_least_64, "0100"))
res = if_flag_from_two_options(ckt, gates_96, res, add_gate_from_tt(ckt, M_at_least_128, m_to_64, "0100"))
res = if_flag_from_two_options(ckt, res_min_in_line_67, res, add_gate_from_tt(ckt, M_from_64_to_128, m_to_64, "0001"))
res = if_flag_from_two_options(ckt, res_min_in_line_69, res, M_to_64)
res = if_flag_from_two_options(ckt, res_min_line_71, res, add_gate_from_tt(ckt, M_at_least_192, m_at_least_192, "0010"))

for gate in res:
    ckt.mark_as_output(gate)
ckt.into_bench()
ckt = RemoveRedundantGates().transform(ckt)
ckt.save_to_file(f"ex160.bench")

