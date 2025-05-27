
import cirbo.synthesis.generation.arithmetics
import cirbo.core
from cirbo.core import Circuit, Gate
from cirbo.core.circuit import INPUT
from cirbo.minimization import RemoveRedundantGates
from cirbo.synthesis.generation import GenerationBasis
from cirbo.synthesis.generation.arithmetics import add_sqrt, add_sum_two_numbers, add_mul, add_div_mod
from cirbo.synthesis.generation.arithmetics._utils import PLACEHOLDER_STR, add_gate_from_tt
from cirbo.synthesis.generation.arithmetics.multiplication import add_mul_our_karatsuba
from cirbo.synthesis.generation.arithmetics.square import add_square
from cirbo.synthesis.generation.arithmetics.summation import add_sum_n_power_bits_naive

ma = {4:"1011", 5:"10001", 6:"101001", 7:"1100001", 8:"11110001"}
for n in range(4, 9):
    ckt = Circuit()
    a = [f'x{n}_{i}' for i in range(n)]
    b = [f'y{n}_{i}' for i in range(n)]
    for i in range(n):
        ckt.add_gate(Gate(a[i], INPUT))
    for i in range(n):
        ckt.add_gate(Gate(b[i], INPUT))

    c = [[PLACEHOLDER_STR] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            c[i][j] = add_gate_from_tt(
                ckt, a[i], b[j], '0001'
            )

    powers = []
    for i in range(n):
        for j in range(n):
            powers.append((i + j, c[i][j]))
    res = add_sum_n_power_bits_naive(ckt, powers, basis= GenerationBasis.AIG)
    # now we need make res % ma[n]
    nul = add_gate_from_tt(ckt, a[0], b[0], '0000')
    ed = add_gate_from_tt(ckt, a[0], b[0], '1111')

    modul = []
    res_labels = [i[1] for i in res]

    for i in reversed(ma[n]):
        if i == "0":
            modul.append(nul)
        else:
            modul.append(ed)
    while len(modul) < len(res_labels):
        modul.append(nul)
    _, res_mod = add_div_mod(ckt, res_labels, modul)
    res_mod = res_mod[:n]
    for gate in res_mod:
        ckt.mark_as_output(gate)
    ckt.into_bench()
    ckt = RemoveRedundantGates().transform(ckt)
    # print(ckt.gates_number())
    ckt.save_to_file(f"mult_mod{n}.bench")
# print(ckt.evaluate([0 for i in range(2 * n)]))
# print(ckt.evaluate([1, 1, 1, 1, 0, 0, 0, 0]))
# for arr in ans:
#     print([int(i) for i in arr])
# print(ckt.get_truth_table())

