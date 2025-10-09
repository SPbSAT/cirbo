import typing as tp
from collections import deque
from itertools import zip_longest
from sortedcontainers import SortedList


from cirbo.core.circuit import Circuit, gate

from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
    validate_const_size,
)
from cirbo.synthesis.generation.exceptions import BadBasisError
from cirbo.synthesis.generation.helpers import GenerationBasis


__all__ = [
    "generate_sum_n_bits",
    "add_sum2",
    "add_sum3",
    "add_sum_n_bits",
    "add_sum_n_bits_easy",
    "add_sum_pow2_m1",
    "add_sum_two_numbers",
    "add_sum_two_numbers_log_depth",
    "add_sum_two_numbers_log_depth_Brent_Kung",
    "add_sum_two_numbers_with_shift",
    "add_sum_n_weighted_bits",
    "add_sum_n_weighted_bits_log_depth", 
    "add_sum_n_weighted_bits_naive",
    "generate_sum_weighted_bits_efficient",
    "generate_sum_weighted_bits_naive",
    "mdfa_sum_weighted_bits",
]


def add_sum_two_numbers(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Function to add two binary numbers represented by input labels.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the sum of the two numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if n < m:
        n, m = m, n
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
    d = [[PLACEHOLDER_STR] for _ in range(n + 1)]
    d[0] = add_sum_n_bits(circuit, [input_labels_a[0], input_labels_b[0]], basis=basis)
    for i in range(1, n):
        inp = [d[i - 1][1], input_labels_a[i]]
        if i < m:
            inp.append(input_labels_b[i])
        d[i] = list(add_sum_n_bits(circuit, inp, basis=basis))
    d[n] = [d[n - 1][1]]
    return reverse_if_big_endian([d[i][0] for i in range(n + 1)], big_endian)


def xor_two_bits(
    circuit: Circuit,
    a: gate.Label, 
    b: gate.Label,
    *, 
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> gate.Label:
    if isinstance(basis, str):
        _basis = GenerationBasis(basis.upper())
    else:
        _basis = basis

    if(_basis == GenerationBasis.XAIG):
        return add_gate_from_tt(circuit, a, b, '0110')
    if(basis == GenerationBasis.AIG):
        ab = add_gate_from_tt(circuit, a, b, '0001')
        nab = add_gate_from_tt(circuit, a, b, '1000')
        return add_gate_from_tt(circuit, ab, nab, '1000')


def add_sum_two_numbers_with_shift(
    circuit: Circuit,
    shift,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
) -> list[gate.Label]:  # shift for second
    """
    Function to add two binary numbers with a shift applied to the second number.

    :param circuit: The general circuit.
    :param shift: The number of bit positions to shift the second number.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the sum of the two numbers after applying the
        shift.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)

    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if (
        shift >= n
    ):  # if shift so big for first number (in out cases I hope we will not use this)
        d = [[PLACEHOLDER_STR] for _ in range(m + shift)]
        for i in range(n):
            d[i] = [input_labels_a[i]]
        if shift != n:
            zero = add_gate_from_tt(
                circuit,
                input_labels_a[0],
                input_labels_a[0],
                '0000',
            )
            for i in range(n, shift - n):
                d[i] = [zero]
        for i in range(m):
            d[i + shift] = [input_labels_b[i]]
        return reverse_if_big_endian([i[0] for i in d], big_endian)
    d = [[PLACEHOLDER_STR] for _ in range(max(n, m + shift) + 1)]
    for i in range(shift):
        d[i] = [input_labels_a[i]]
    res_sum = add_sum_two_numbers(circuit, input_labels_a[shift:n], input_labels_b)
    for i in range(shift, max(n, m + shift) + 1):
        d[i] = [res_sum[i - shift]]
    return reverse_if_big_endian(
        [d[i][0] for i in range(max(n, m + shift) + 1)], big_endian
    )


def add_sum_two_numbers_log_depth(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Function to add two binary numbers represented by input labels in O(log(n+m)) depth and O(n*logn) size using Koggle-stone adder.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: List of bits representing the sum of the two numbers.

    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if n < m:
        n, m = m, n
        input_labels_a, input_labels_b = input_labels_b, input_labels_a
    
    zero = add_gate_from_tt(circuit, input_labels_a[0], input_labels_a[0], '0000')

    for i in range(n-m):
        input_labels_b.append(zero)

    p, g = zip(*[add_sum2(circuit, [input_labels_a[i], input_labels_b[i]], basis=basis) for i in range(n)])
    p, g = list(p), list(g)

    po = p.copy()
    d = 1

    while(d < n):
        for i in range(n-1, d-1, -1):
            t = add_gate_from_tt(circuit, p[i], g[i-d], '0001')
            g[i] = add_gate_from_tt(circuit, g[i], t, '0111')

        for i in range(n-1, d-1, -1):
            p[i] = add_gate_from_tt(circuit, p[i], p[i-d], '0001')

        d *= 2

    g = [zero] + g 
    s = [xor_two_bits(circuit, po[i], g[i], basis=basis) for i in range(n)]
    s.append(g[n])
    
    return reverse_if_big_endian(s, big_endian)


def add_sum_two_numbers_log_depth_Brent_Kung(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Add two binary numbers using a Brent–Kung adder.
    Depth: O(log n), Size: O(n).

    :param circuit: The general circuit.
    :param input_labels_a: Bits of first binary number.
    :param input_labels_b: Bits of second binary number.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: Whether numbers are big-endian.
    :return: Bits of the sum.
    """
    input_labels_a = list(input_labels_a)
    input_labels_b = list(input_labels_b)
    n = len(input_labels_a)
    m = len(input_labels_b)
    if big_endian:
        input_labels_a.reverse()
        input_labels_b.reverse()

    if n < m:
        n, m = m, n
        input_labels_a, input_labels_b = input_labels_b, input_labels_a

    zero = add_gate_from_tt(
        circuit, 
        input_labels_a[0], 
        input_labels_a[0], 
        '0000'
    )
    for i in range(n - m):
        input_labels_b.append(zero)

    p, g = zip(*[add_sum2(circuit, [input_labels_a[i], input_labels_b[i]], basis=basis) for i in range(n)])
    p, g = list(p), list(g)

    prefix_p = p.copy()
    prefix_g = g.copy()
    
    s = 1
    while s < n:
        next_s = s * 2
        for i in range(next_s - 1, n, next_s):
            j = i - s
            if j >= 0:
                tmp = add_gate_from_tt(circuit, prefix_p[i], prefix_g[j], '0001')
                new_g = add_gate_from_tt(circuit, prefix_g[i], tmp, '0111')
                new_p = add_gate_from_tt(circuit, prefix_p[i], prefix_p[j], '0001')
                
                prefix_g[i] = new_g
                prefix_p[i] = new_p
        s = next_s

    s //= 2
    while s > 1:
        next_s = s // 2
        for i in range(s - 1, n, s):
            if i + next_s < n:
                j = i + next_s
                tmp = add_gate_from_tt(circuit, prefix_p[j], prefix_g[i], '0001')
                new_g = add_gate_from_tt(circuit, prefix_g[j], tmp, '0111')
                new_p = add_gate_from_tt(circuit, prefix_p[j], prefix_p[i], '0001')
                
                prefix_g[j] = new_g
                prefix_p[j] = new_p
        s = next_s

    carries = [zero]
    for i in range(n - 1):
        carries.append(prefix_g[i])
    
    sum_bits = []
    for i in range(n):
        sum_bit = xor_two_bits(circuit, p[i], carries[i], basis=basis)
        sum_bits.append(sum_bit)
    
    sum_bits.append(prefix_g[n-1])
    
    return reverse_if_big_endian(sum_bits, big_endian)


def add_sum_n_weighted_bits_log_depth(
    circuit: Circuit,
    input_labels_with_pow: tp.Iterable[tuple[int, gate.Label]],
    *, 
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[tuple[int, gate.Label]]:
    """
    Function to add a variable number of bits using Full and Half adders.
    Depth: O(log n), Size: O(n).

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: Tuple containing the sum in binary representation.
    """
    input_labels_with_pow = list(input_labels_with_pow)
    c = {}
    for p in input_labels_with_pow:
        c.setdefault(p[0], []).append(p[1])

    while(max(len(c[i]) for i in c.keys()) > 2):
        cn = {}
        for key in c:
            for i in range(0, len(c[key]), 3):
                inp = []
                for k in range(i, i + 3):
                    if len(c[key]) > k:
                        inp.append(c[key][k])

                if len(inp) > 0:
                    res = add_sum_n_bits(circuit, inp, basis=basis)
                    for k in range(len(res)):
                        cn.setdefault(key+k, []).append(res[k])
        c = cn

    consec = []
    last = -1
    zero = add_gate_from_tt(
        circuit, 
        input_labels_with_pow[0][1], 
        input_labels_with_pow[0][1], 
        '0000'
    )
    ans = []

    def sum_block():
        input_labels_a = []
        input_labels_b = []
        for p in consec:
            input_labels_a.append(p[0])
            if len(p) == 1:
                input_labels_b.append(zero)
            else:
                input_labels_b.append(p[1])

        sum = add_sum_two_numbers_log_depth_Brent_Kung(circuit, input_labels_a, input_labels_b, basis=basis)
        for i in range(len(sum)):
            ans.append([last-len(consec)+1+i, sum[i]])

    for k in sorted(c.keys()):
        if(last == -1 or last == k-1):
            consec.append(c[k])
            last = k
        else:
            sum_block()
            last = k
            consec =[c[k]]
    
    sum_block()
    return ans     


def mdfa_sum_weighted_bits(
    circuit: Circuit,
    input_labels_with_pow: tp.Iterable[tuple[int, gate.Label]],
) -> list[tuple[int, gate.Label]]:
    """
    Function to add a variable number of bits with using MDFA. Has better size and worse depth than add_sum_n_weighted_bits_log_depth.
    Depth: O(log n), Size: O(n).
    MDFA does not work in AIG basis, so no basis parameter, just use add_sum_n_weighted_bits_log_depth.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :return: Tuple containing the sum in binary representation.
    """
    c = {}
    d = {}
    for p in input_labels_with_pow:
        c.setdefault(p[0], deque()).append(p[1])
 
    while(max(len(c.get(i, deque())) + len(d.get(i, deque())) for i in set(c) | set(d)) > 6):
        cn = {}
        dn = {}
        for key in set(c) | set(d):
            single = c.get(key, deque()).copy()  
            pairs = d.get(key, deque()).copy()  

            while(len(single) >= 1 and len(pairs) >= 4):
                z, x, xy = add_mdfa(circuit, [single.popleft()] + [pairs.popleft() for _ in range(4)])
                cn.setdefault(key, deque()).append(z)
                dn.setdefault(key+1, deque()).extend([x, xy])

            while(len(single) >= 3 and len(pairs) >= 2):
                a1, b1 = single.popleft(), single.popleft()
                ab1 = add_gate_from_tt(
                    circuit, 
                    a1, 
                    b1, 
                    "0110",
                )
                a2, ab2 = pairs.popleft(), pairs.popleft()
                z, x, xy = add_mdfa(circuit, [single.popleft(), a1, ab1, a2, ab2])
                cn.setdefault(key, deque()).append(z)
                dn.setdefault(key+1, deque()).extend([x, xy])

            while(len(single) >= 5):
                a1, b1 = single.popleft(), single.popleft()
                ab1 = add_gate_from_tt(
                    circuit, 
                    a1, 
                    b1, 
                    "0110",
                )
                a2, b2 = single.popleft(), single.popleft()
                ab2 = add_gate_from_tt(
                    circuit, 
                    a2,
                    b2, 
                    "0110",
                )
                z, x, xy = add_mdfa(circuit, [single.popleft(), a1, ab1, a2, ab2])
                cn.setdefault(key, deque()).append(z)
                dn.setdefault(key+1, deque()).extend([x, xy])
            if(len(single) == 4):
                res = add_sum_n_bits(circuit, [single.popleft() for _ in range(3)])
                cn.setdefault(key, deque()).extend([res[0], single.popleft()])
                cn.setdefault(key+1, deque()).append(res[1])

            while(len(pairs) >= 10):
                a, ab = pairs.popleft(), pairs.popleft()
                b = add_gate_from_tt(
                    circuit, 
                    a, 
                    ab, 
                    "0110",
                )
                for e in [a, b]:
                    z, x, xy = add_mdfa(circuit, [e] + [pairs.popleft() for _ in range(4)])
                    cn.setdefault(key, deque()).append(z)
                    dn.setdefault(key+1, deque()).extend([x, xy])
            while(len(pairs) >= 4):
                z, x, xy = add_simplified_mdfa(circuit, [pairs.popleft() for _ in range(4)])
                cn.setdefault(key, deque()).append(z)
                dn.setdefault(key+1, deque()).extend([x, xy])
            
            cn.setdefault(key, deque()).extend(single)
            dn.setdefault(key, deque()).extend(pairs)

        c = cn
        d = dn

    weighted_bits = []
    for key, value in c.items():
        for i in value:
            weighted_bits.append([key, i])
    for key, value in d.items():
        for i in range(0, len(value), 2):
            a, ab = value[i], value[i+1]
            b = add_gate_from_tt(
                circuit, 
                a, 
                ab, 
                "0110",
            )
            weighted_bits.append([key, a])
            weighted_bits.append([key, b])
    return add_sum_n_weighted_bits_log_depth(circuit, weighted_bits) 


def add_sum2(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[gate.Label]:
    if(basis==GenerationBasis.AIG):
        return add_sum2_aig(circuit, input_labels)
    
    input_labels = list(input_labels)
    validate_const_size(input_labels, 2)
    [x1, x2] = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    return list([g1, g2])


def add_sum3(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x3 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0110')
    g2 = add_gate_from_tt(circuit, x2, x3, '0110')
    g3 = add_gate_from_tt(circuit, g1, g2, '0111')
    g4 = add_gate_from_tt(circuit, g1, x3, '0110')
    g5 = add_gate_from_tt(circuit, g3, g4, '0110')
    return list([g4, g5])


# given x1, x2, and (x2 oplus x3), computes the binary representation
# of (x1 + x2 + x3)
def add_stockmeyer_block(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x23 = input_labels
    w0 = add_gate_from_tt(circuit, x1, x23, '0110')
    g2 = add_gate_from_tt(circuit, x2, x23, '0010')
    g3 = add_gate_from_tt(circuit, x1, x23, '0001')
    w1 = add_gate_from_tt(circuit, g2, g3, '0110')
    return list([w0, w1])


def add_mdfa(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 5)
    z, x1, xy1, x2, xy2 = input_labels
    g1 = add_gate_from_tt(circuit, x1, z, '0110')
    g2 = add_gate_from_tt(circuit, xy1, g1, '0111')
    g3 = add_gate_from_tt(circuit, xy1, z, '0110')
    g4 = add_gate_from_tt(circuit, g2, g3, '0110')
    g5 = add_gate_from_tt(circuit, x2, g3, '0110')
    g6 = add_gate_from_tt(circuit, g3, xy2, '0110')
    g7 = add_gate_from_tt(circuit, g5, xy2, '0010')
    g8 = add_gate_from_tt(circuit, g2, g7, '0110')
    return list([g6, g4, g8])


# an MDFA block with z=0
def add_simplified_mdfa(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 4)
    x1, xy1, x2, xy2 = input_labels
    g2 = add_gate_from_tt(circuit, xy1, x1, '0111')
    g4 = add_gate_from_tt(circuit, g2, xy1, '0110')
    g5 = add_gate_from_tt(circuit, x2, xy1, '0110')
    g6 = add_gate_from_tt(circuit, xy1, xy2, '0110')
    g7 = add_gate_from_tt(circuit, g5, xy2, '0010')
    g8 = add_gate_from_tt(circuit, g2, g7, '0110')
    return list([g6, g4, g8])


def add_sum_n_bits_easy(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label], *, big_endian: bool = False
) -> list[gate.Label]:
    """
    Function to add a variable number of bits with numbers of gate approximately 5 * n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: Tuple containing the sum in binary representation.

    """
    now = list(input_labels)
    if big_endian:
        now.reverse()
    res = []
    while len(now) > 0:
        next = []
        while len(now) > 2:
            x, y = add_sum3(circuit, now[-1:-4:-1])
            for _ in range(3):
                now.pop()
            now.append(x)
            next.append(y)
        while len(now) > 1:
            x, y = add_sum2(circuit, now[-1:-3:-1])
            for _ in range(2):
                now.pop()
            now.append(x)
            next.append(y)
        res.append(now[0])
        now = next
    return reverse_if_big_endian(res, big_endian)


def add_sum2_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 2)
    x1, x2 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0111')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    g3 = add_gate_from_tt(circuit, g1, g2, '0010')
    return list([g3, g2])


def add_sum3_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    input_labels = list(input_labels)
    validate_const_size(input_labels, 3)
    x1, x2, x3 = input_labels
    g1 = add_gate_from_tt(circuit, x1, x2, '0111')
    g2 = add_gate_from_tt(circuit, x1, x2, '0001')
    g3 = add_gate_from_tt(circuit, g1, g2, '0010')
    g4 = add_gate_from_tt(circuit, g3, x3, '0111')
    g5 = add_gate_from_tt(circuit, g3, x3, '0001')
    g6 = add_gate_from_tt(circuit, g4, g5, '0010')
    g7 = add_gate_from_tt(circuit, g2, g5, '0111')
    return list([g6, g7])


def generate_sum_n_bits(
    n: int,
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> Circuit:
    """
    Generates a circuit that have sum of n bits in result. In fact, it is the same as
    generate_sum_weighted_bits_efficient([0] * n). See this function for more details.

    :param n: number of input bits
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format

    """
    circuit = Circuit.bare_circuit(n)
    res = add_sum_n_bits(
        circuit,
        circuit.inputs,
        basis=basis,
        big_endian=big_endian,
    )
    circuit.set_outputs(res)
    return circuit


def generate_sum_weighted_bits_efficient(
    weights: tp.Iterable[int],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> Circuit:
    """
    Global task: for given weights w_0, ..., w_{n - 1}
    make circuit with input gates inp_0, ... inp_{n - 1} and output gates
    out_0, ..., out_{m - 1} with the main property inp_0 * 2^{w_0} + ...
    inp_{n - 1} * 2^{w_{n - 1}} = out_0 * 2^{out_w_0} + ... + out_{m - 1} * 2^{out_w{m - 1}}.
    This function will find circuit with minimum possible m. Number of gates
    will be not more than 4.5 * n - 2 * m in xaig and 7 * n - 3 * m in aig.

    :param weights: list of weights to be created and summed after. i-th input is
    correspond to i-th number from the list.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    """
    weights = list(weights)
    n = len(weights)
    circuit = Circuit.bare_circuit(n)
    powers_with_labels = [(weights[i], circuit.inputs[i]) for i in range(n)]
    res = add_sum_n_weighted_bits(circuit, powers_with_labels, basis=basis)
    res_labels = [i[1] for i in res]
    circuit.set_outputs(res_labels)
    return circuit


def generate_sum_weighted_bits_naive(
    weights: tp.Iterable[int],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> Circuit:
    """
    Global task: for given weights w_0, ..., w_{n - 1}
    make circuit with input gates inp_0, ... inp_{n - 1} and output gates
    out_0, ..., out_{m - 1} with the main property
    inp_0 * 2^{w_0} + ... + inp_{n - 1} * 2^{w_{n - 1}} =
    = out_0 * 2^{out_w_0} + ... + out_{m - 1} * 2^{out_w{m - 1}}.
    This function will find circuit with minimum possible m. Number of gates
    will be not more than 5 * n - 2 * m in xaig and 7 * n - 3 * m in aig.
    General difference between this and efficient version only in gate count.

    :param weights: list of weights to be created and summed after. i-th input is
    correspond to i-th number from the list.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    """
    weights = list(weights)
    n = len(weights)
    circuit = Circuit.bare_circuit(n)
    powers_with_labels = [(weights[i], circuit.inputs[i]) for i in range(n)]
    res = add_sum_n_weighted_bits_naive(circuit, powers_with_labels, basis=basis)
    res_labels = [i[1] for i in res]
    circuit.set_outputs(res_labels)
    return circuit


def add_sum_n_bits(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Global task: for given input gates inp_0, ... inp_{n - 1}, build and add
    sub circuit with output gates out_0, ..., out_{m - 1} with the main property
    inp_0 * 2^{w_0} + ... + inp_{n - 1} * 2^{w_{n - 1}} =
    = out_0 * 2^{out_w_0} + ... + out_{m - 1} * 2^{out_w{m - 1}}.
    This function will find circuit with minimum
    possible m. Number of gates will be not more than 4.5 * n - 2 * m in xaig
    and 7 * n - 3 * m in aig.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: list containing labels of sum bits.

    """

    input_labels = list(input_labels)
    if big_endian:
        input_labels.reverse()

    if isinstance(basis, str):
        _basis = GenerationBasis(basis.upper())
    else:
        _basis = basis

    if _basis == GenerationBasis.XAIG:
        return reverse_if_big_endian(
            _add_sum_n_bits(
                circuit=circuit,
                input_labels=input_labels,
            ),
            big_endian,
        )
    if _basis == GenerationBasis.AIG:
        return reverse_if_big_endian(
            _add_sum_n_bits_aig(
                circuit=circuit,
                input_labels=input_labels,
            ),
            big_endian,
        )
    raise BadBasisError(f"Unsupported basis: {basis}.")


def _add_sum_n_bits_aig(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    """
    Function to add a variable number of bits IN AIG basis with numbers of gate
    approximately 7 * n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :return: Tuple containing the sum in binary representation.

    """
    now = list(input_labels)
    res = []
    while len(now) > 0:
        next = []
        while len(now) > 2:
            x, y = add_sum3_aig(circuit, now[-1:-4:-1])
            for _ in range(3):
                now.pop()
            now.append(x)
            next.append(y)
        if len(now) > 1:
            x, y = add_sum2_aig(circuit, now[-1:-3:-1])
            for _ in range(2):
                now.pop()
            now.append(x)
            next.append(y)
        res.append(now[0])
        now = next
    return res


def _add_sum_n_bits(
    circuit: Circuit, input_labels: tp.Iterable[gate.Label]
) -> list[gate.Label]:
    """
    Function to add a variable number of bits with numbers of gate not more than 4.5 *
    n.

    :param circuit: The general circuit.
    :param input_labels: List of bits to be added.
    :return: Tuple containing the sum in binary representation.

    """
    res = []
    now_x_xy = []
    now_solo = list(input_labels)
    while len(now_solo) > 1:
        xy = add_gate_from_tt(circuit, now_solo[-1], now_solo[-2], "0110")
        now_x_xy.append((now_solo[-1], xy))
        for _ in range(2):
            now_solo.pop()

    while len(now_solo) > 0 or len(now_x_xy) > 0:
        next_solo = []
        next_x_xy = []
        while len(now_x_xy) > 1:
            if len(now_solo) > 0:
                z, x1, x1y1 = add_mdfa(
                    circuit,
                    [
                        now_solo[-1],
                        now_x_xy[-1][0],
                        now_x_xy[-1][1],
                        now_x_xy[-2][0],
                        now_x_xy[-2][1],
                    ],
                )
                for _ in range(2):
                    now_x_xy.pop()
                now_solo.pop()

                now_solo.append(z)
                next_x_xy.append((x1, x1y1))
            else:
                now_solo.append(now_x_xy[-1][1])
                next_solo.append(
                    add_gate_from_tt(circuit, now_x_xy[-1][0], now_x_xy[-1][1], "0010")
                )
                now_x_xy.pop()
        if len(now_x_xy) == 1:
            if len(now_solo) > 0:
                x, y = add_stockmeyer_block(
                    circuit, [now_solo[-1], now_x_xy[-1][0], now_x_xy[-1][1]]
                )
                now_solo.pop()
                now_x_xy.pop()
                next_solo.append(y)
                now_solo.append(x)
            else:
                now_solo.append(now_x_xy[-1][1])
                next_solo.append(
                    add_gate_from_tt(circuit, now_x_xy[-1][0], now_x_xy[-1][1], "0010")
                )
                now_x_xy.pop()

        while len(now_solo) > 2:
            x, y = add_sum3(circuit, now_solo[-1:-4:-1])
            for _ in range(3):
                now_solo.pop()
            now_solo.append(x)
            next_solo.append(y)
        if len(now_solo) > 1:
            x, y = add_sum2(circuit, now_solo[-1:-3:-1])
            for _ in range(2):
                now_solo.pop()
            now_solo.append(x)
            next_solo.append(y)
        res.append(now_solo[0])
        now_solo = next_solo
        now_x_xy = next_x_xy
    return res


def add_sum_n_weighted_bits_naive(
    circuit: Circuit,
    input_labels_with_pow: tp.Iterable[tuple[int, gate.Label]],
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[tuple[int, gate.Label]]:
    """
    Global task: for given weights w_0, ..., w_{n - 1} and input gates
    inp_0, ... inp_{n - 1}, build and add sub circuit with output gates
    out_0, ..., out_{m - 1} with the main property inp_0 * w_0 + ...
    inp_0 * 2^{w_0} + ... + inp_{n - 1} * 2^{w_{n - 1}} =
    = out_0 * 2^{out_w_0} + ... + out_{m - 1} * 2^{out_w{m - 1}}.
    This function will find circuit with minimum possible m. Number of gates
    will be not more than 5 * n - 3 * m in xaig and 7 * n - 3 * m in aig.

    :param circuit: The general circuit.
    :param input_labels_with_pow: List of pairs with format (power, label) to be added.
    :return: Tuple containing the result of sumation in format list[tuple[int, gate.Label]].

    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    """

    res = []
    input_labels_with_pow = list(input_labels_with_pow)
    single = SortedList(input_labels_with_pow)  # sorted list of single
    pairs = SortedList()  # sorted list of pairs

    inf = max([i[0] for i in input_labels_with_pow]) + len(input_labels_with_pow) + 1
    inf_label = "inf_label"
    single.add((inf, inf_label))
    pairs.add((inf, inf_label, inf_label))

    while len(single) > 1 or len(pairs) > 1:
        lev_single, _ = single[0]
        lev_pairs, _, _ = pairs[0]
        now_level = min(lev_single, lev_pairs)
        if now_level == inf:
            break
        now_singles = []
        now_pairs = []
        while single[0][0] == now_level:
            now_singles.append(single[0][1])
            single.discard(single[0])
        while pairs[0][0] == now_level:
            now_pairs.append((pairs[0][1], pairs[0][2]))
            pairs.discard(pairs[0])
        now_solo = now_singles
        while len(now_solo) > 2:
            x, y, z = now_solo[-1], now_solo[-2], now_solo[-3]
            if basis == GenerationBasis.AIG:
                now_level_gate, next_level_gate = add_sum3_aig(circuit, [x, y, z])
            else:
                now_level_gate, next_level_gate = add_sum3(circuit, [x, y, z])
            for _ in range(3):
                now_solo.pop()
            now_solo.append(now_level_gate)
            single.add((now_level + 1, next_level_gate))

        if len(now_solo) == 2:
            x, y = now_solo[-1], now_solo[-2]
            if basis == GenerationBasis.AIG:
                now_level_gate, next_level_gate = add_sum2_aig(circuit, [x, y])
            else:
                now_level_gate, next_level_gate = add_sum2(circuit, [x, y])
            for _ in range(2):
                now_solo.pop()
            now_solo.append(now_level_gate)
            single.add((now_level + 1, next_level_gate))

        res.append((now_level, now_solo[0]))
    return res


def add_sum_n_weighted_bits(
    circuit,
    input_labels_with_pow,
    *,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[tuple[int, gate.Label]]:
    """
    Global task: for given weights w_0, ..., w_{n - 1} and input gates
    inp_0, ... inp_{n - 1}, build and add sub circuit with output gates
    out_0, ..., out_{m - 1} with the main property inp_0 * w_0 + ...
    inp_0 * 2^{w_0} + ... + inp_{n - 1} * 2^{w_{n - 1}} =
    = out_0 * 2^{out_w_0} + ... + out_{m - 1} * 2^{out_w{m - 1}}.
    This function will find circuit with minimum possible m. Number of gates
    will be not more than 4.5 * n - 2 * m in xaig and 7 * n - 3 * m in aig.

    :param circuit: The general circuit.
    :param input_labels_with_pow: List of pairs with format (power, label) to be added.
    :return: Tuple containing the sum in binary representation.

    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    """

    res = []

    single = SortedList(list(input_labels_with_pow))  # sorted list of single
    pairs = SortedList()  # sorted list of pairs
    inf = max([i[0] for i in input_labels_with_pow]) + len(input_labels_with_pow) + 1
    inf_label = "inf_label"
    single.add((inf, inf_label))
    pairs.add((inf, inf_label, inf_label))

    while len(single) > 1 or len(pairs) > 1:
        lev_single, _ = single[0]
        lev_pairs, _, _ = pairs[0]
        now_level = min(lev_single, lev_pairs)
        if now_level == inf:
            break
        now_singles = []
        now_pairs = []
        while single[0][0] == now_level:
            now_singles.append(single[0][1])
            single.discard(single[0])
        while pairs[0][0] == now_level:
            now_pairs.append((pairs[0][1], pairs[0][2]))
            pairs.discard(pairs[0])

        next_solo = []
        next_x_xy = []
        now_x_xy = now_pairs
        now_solo = now_singles

        if basis == GenerationBasis.AIG:
            while len(now_solo) > 2:
                x, y, z = now_solo[-1], now_solo[-2], now_solo[-3]
                now_level_gate, next_level_gate = add_sum3_aig(circuit, [x, y, z])
                for _ in range(3):
                    now_solo.pop()
                now_solo.append(now_level_gate)
                single.add((now_level + 1, next_level_gate))

            if len(now_solo) == 2:
                x, y = now_solo[-1], now_solo[-2]
                now_level_gate, next_level_gate = add_sum2_aig(circuit, [x, y])
                for _ in range(2):
                    now_solo.pop()
                now_solo.append(now_level_gate)
                single.add((now_level + 1, next_level_gate))

            res.append((now_level, now_solo[0]))
            continue

        while len(now_solo) > 1:
            xy = add_gate_from_tt(circuit, now_solo[-1], now_solo[-2], "0110")
            now_x_xy.append((now_solo[-1], xy))
            for _ in range(2):
                now_solo.pop()

        while len(now_x_xy) > 1:
            if len(now_solo) > 0:
                z, x1, x1y1 = add_mdfa(
                    circuit,
                    [
                        now_solo[-1],
                        now_x_xy[-1][0],
                        now_x_xy[-1][1],
                        now_x_xy[-2][0],
                        now_x_xy[-2][1],
                    ],
                )
                for _ in range(2):
                    now_x_xy.pop()
                now_solo.pop()

                now_solo.append(z)
                next_x_xy.append((x1, x1y1))
            else:
                now_solo.append(now_x_xy[-1][1])
                next_solo.append(
                    add_gate_from_tt(circuit, now_x_xy[-1][0], now_x_xy[-1][1], "0010")
                )
                now_x_xy.pop()
        if len(now_x_xy) == 1:
            if len(now_solo) > 0:
                x, y = add_stockmeyer_block(
                    circuit, [now_solo[-1], now_x_xy[-1][0], now_x_xy[-1][1]]
                )
                now_solo.pop()
                now_x_xy.pop()
                next_solo.append(y)
                now_solo.append(x)
            else:
                now_solo.append(now_x_xy[-1][1])
                next_solo.append(
                    add_gate_from_tt(circuit, now_x_xy[-1][0], now_x_xy[-1][1], "0010")
                )
                now_x_xy.pop()

        res.append((now_level, now_solo[0]))

        for label in next_solo:
            single.add((now_level + 1, label))
        for labels in next_x_xy:
            pairs.add((now_level + 1, labels[0], labels[1]))

    return res


# divides the sum into blocks of size 2^n-1
# will be replaced with calls of 4.5n sums generator
def add_sum_pow2_m1(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: tp.Union[str, GenerationBasis] = GenerationBasis.XAIG,
) -> list[list[gate.Label]]:
    input_labels = list(input_labels)
    n = len(input_labels)
    assert n > 0
    if n == 1:
        return [reverse_if_big_endian([input_labels[0]], big_endian)]

    out = []
    it = 0
    while len(input_labels) > 2:
        for pw in range(5, 1, -1):
            i = 2**pw - 1
            while len(input_labels) >= i:
                out.append(add_sum_n_bits(circuit, input_labels[0:i], basis=basis))
                input_labels = input_labels[i:]
                input_labels.append(out[it][0])
                it += 1

    if len(input_labels) == 2:
        out.append(add_sum2(circuit, input_labels[0:2]))
        input_labels = input_labels[2:]
        input_labels.append(out[it][0])

    out = [list(filter(None, x)) for x in zip_longest(*out)]
    out[0] = [out[0][len(out[0]) - 1]]
    return [reverse_if_big_endian(i, big_endian) for i in out]
