from boolean_circuit_tool.generation.arithmetics.add_n_bits_sum import add_sub2, add_sub3
from boolean_circuit_tool.generation.arithmetics.add_gate_from_TT import add_gate_with_TT
from boolean_circuit_tool.core.circuit import Circuit, Gate
from boolean_circuit_tool.core.circuit.gate import Gate, INPUT

def add_sub_with_per_equal_size(circuit, input_labels_a, input_labels_b):
    n = len(input_labels_a)
    assert n == len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    res = [0] * n
    bal = [0] * n
    res[0], bal[0] = add_sub2(circuit, [input_labels_a[0], input_labels_b[0]])
    for i in range(1, n):
        res[i], bal[i] = add_sub3(circuit, [input_labels_a[i], input_labels_b[i], bal[i - 1]])
    return res, bal[n - 1]


def add_div_mod(circuit, input_labels_a, input_labels_b):  # return n bits for result div and n bits for result mod
    n = len(input_labels_a)
    assert n == len(input_labels_b)
    for input_label in input_labels_a:
        assert circuit.has_element(input_label)
    for input_label in input_labels_b:
        assert circuit.has_element(input_label)

    a = input_labels_a
    b = input_labels_b
    pref = [b[n - 1]]  # larger bit in b
    for i in range(n - 2, 0, -1):
        pref.append(add_gate_with_TT(circuit, pref[-1], b[i], "0111"))
    result = [0] * n
    now = a
    for i in range(n - 1, 0, -1):  # chose shift for sub (> 0)
        prov = pref[i - 1]
        m = n - i # intersection
        sub_res, per = add_sub_with_per_equal_size(circuit, now[(n - m):], b[:m])
        result[i] = add_gate_with_TT(circuit, prov, per, "1000")
        for j in range(m):
            now[j + n - m] = add_gate_with_TT(circuit, add_gate_with_TT(circuit, result[i], sub_res[j], "0001"), add_gate_with_TT(circuit, now[j + n - m], result[i], "0010"), "0111")
    m = n  # intersection
    sub_res, per = add_sub_with_per_equal_size(circuit, now, b)
    result[0] = add_gate_with_TT(circuit, per, per, "1000")
    for j in range(m):
        now[j] = add_gate_with_TT(circuit, add_gate_with_TT(circuit, result[0], sub_res[j], "0001"),
                                          add_gate_with_TT(circuit, now[j], result[0], "0010"), "0111")

    # if we need result A % 0 = 0 and B / 0 = 0
    pref.append(add_gate_with_TT(circuit, pref[-1], b[0], "0111"))
    for i in range(n):
        result[i] = add_gate_with_TT(circuit, result[i], pref[-1], "0001")
    for i in range(n):
        now[i] = add_gate_with_TT(circuit, now[i], pref[-1], "0001")

    return result, now



if __name__ == '__main__':
    ckt = Circuit()
    n = 16
    input_labels = [f'x{i}' for i in range(n)]
    for i in range(n):
        ckt.add_gate(Gate(input_labels[i], INPUT))
    res1, res2 = add_div_mod(ckt, input_labels[:(n // 2)], input_labels[(n // 2):])
    for i in res1:
        ckt.mark_as_output(i)

    print(ckt.elements_number)