import cirbo.synthesis.generation.arithmetics
import cirbo.core
from cirbo.core import Circuit, Gate
from cirbo.core.circuit import INPUT
from cirbo.minimization import RemoveRedundantGates
from cirbo.synthesis.generation.arithmetics import add_sqrt, add_sum_two_numbers
from cirbo.synthesis.generation.arithmetics.square import add_square


ckt = Circuit()
n = 8
a = [f'x{i}' for i in range(n)]
b = [f'y{i}' for i in range(n)]
for i in range(n):
    ckt.add_gate(Gate(a[i], INPUT))
for i in range(n):
    ckt.add_gate(Gate(b[i], INPUT))

res_a_sq = add_square(ckt, a)
rea_b_sq = add_square(ckt, b)
res_ab_sum = add_sum_two_numbers(ckt, res_a_sq, rea_b_sq)
res = add_sqrt(ckt, res_ab_sum)
# res = add_sqrt(ckt, a)
for gate in res:
    ckt.mark_as_output(gate)
ckt.into_bench()
ckt = RemoveRedundantGates().transform(ckt)
ckt.save_to_file(f"hypotenuse{n}.bench")
ans = ckt.get_truth_table()
# print(ckt.evaluate([0 for i in range(2 * n)]))
# print(ckt.evaluate([1, 1, 1, 1, 0, 0, 0, 0]))
# for arr in ans:
#     print([int(i) for i in arr])
# print(ckt.get_truth_table())


def custom_function(a, b):
    m, M = min(a, b), max(a, b)

    if M >= 224:
        return 224
    elif m >= 192:
        return 224
    elif 192 <= M < 224 and m < 64:
        return min(2 * M - m - 192, M - m // 2)
    elif 192 <= M < 224 and 64 <= m < 96:
        if M - m > 128:
            return 2 * (M - m - 64)
        else:
            return 2 * (128 - (M - m))
    elif 192 <= M < 224 and 96 <= m < 128:
        return 96
    elif 128 <= M < 224 and 96 <= m < 128:
        return 96  # <-- ТВОЙ СЛУЧАЙ
    elif 128 <= M < 192 and 64 <= m < 96:
        return min(64 + (2 * m - M), 64 + m - M // 2) # don't work some like 64 + min(...)
    elif 128 <= M < 192 and m < 64:
        if M - m > 128:
            return M - m
        else:
            return 128 - (M - m)
    elif 128 <= a < 192 and 128 <= b < 192:
        return min(a + b - 128, (a + b + 1) // 2 + 32)
    elif m >= 64 and M < 128:
        return 96
    elif m < 64 and 64 <= M < 128:
        return min(96, (m + 1) // 2 + M)
    elif a < 64 and b < 64:
        return min(a + b, (a + b + 1) // 2 + 32)
    elif m < 192 and M >= 192:
        return min(224, M + (m + 1) // 2 - 64)

    return 0  # fallback

