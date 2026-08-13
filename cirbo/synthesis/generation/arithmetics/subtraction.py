import typing as tp

from cirbo.core.circuit import Circuit, gate
from cirbo.synthesis.generation.arithmetics._utils import (
    add_gate_from_tt,
    PLACEHOLDER_STR,
    reverse_if_big_endian,
    validate_const_size,
    validate_equal_sizes,
)
from cirbo.synthesis.generation.arithmetics.summation import xor_two_bits
from cirbo.synthesis.generation.exceptions import BadBasisError
from cirbo.synthesis.generation.helpers import GenerationBasis


__all__ = [
    "add_sub2",
    "add_sub3",
    "add_sub_two_numbers",
    "add_sub_two_numbers_log_depth",
    "add_subtract_with_compare",
    "add_subtract_with_compare_log_depth",
    "generate_sub_two_numbers",
]


def generate_sub_two_numbers(
    size_of_input_a: int,
    size_of_input_b: int,
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> Circuit:
    """
    Generates a circuit that have subtract two binary numbers in result.

    :param size_of_input_a: the number of inputs representing the first number.
    :param size_of_input_b: the number of inputs representing the second number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: circuit that difference of the two numbers.

    """

    circuit = Circuit.bare_circuit(size_of_input_a + size_of_input_b)
    outputs = add_sub_two_numbers(
        circuit,
        circuit.inputs[:size_of_input_a],
        circuit.inputs[size_of_input_a:],
        big_endian=big_endian,
        basis=basis,
    )
    circuit.set_outputs(outputs)
    return circuit


def add_sub2(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    _input_labels = list(input_labels)
    if big_endian:
        _input_labels.reverse()
    validate_const_size(_input_labels, 2)
    [x1, x2] = _input_labels

    if basis == GenerationBasis.XAIG:
        g1 = add_gate_from_tt(circuit, x1, x2, '0110')
        g2 = add_gate_from_tt(circuit, x1, x2, '0100')

        return list([g1, g2])  # res and balance
    elif basis == GenerationBasis.AIG:
        g1 = add_gate_from_tt(circuit, x1, x2, '0100')
        g2 = add_gate_from_tt(circuit, x1, x2, '0010')
        g3 = add_gate_from_tt(circuit, g1, g2, '0111')

        return [g3, g1]
    else:
        raise BadBasisError(f"Unsupported basis: {basis}")


def add_sub3(
    circuit: Circuit,
    input_labels: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    _input_labels = list(input_labels)
    if big_endian:
        _input_labels.reverse()
    validate_const_size(_input_labels, 3)

    if basis == GenerationBasis.XAIG:
        x0, x1, x2 = _input_labels  # A, B and balance (we do A - B)
        x3 = add_gate_from_tt(circuit, x0, x1, '0110')
        x4 = add_gate_from_tt(circuit, x1, x2, '0110')
        x5 = add_gate_from_tt(circuit, x3, x4, '0111')
        x6 = add_gate_from_tt(circuit, x2, x3, '0110')
        x7 = add_gate_from_tt(circuit, x0, x5, '0110')
        return list([x6, x7])
    elif basis == GenerationBasis.AIG:
        x0, x1, x2 = _input_labels  # A, B and balance (we do A - B)
        s3 = add_gate_from_tt(circuit, x0, x1, '1101')
        s4 = add_gate_from_tt(circuit, x0, x1, '0100')
        s5 = add_gate_from_tt(circuit, s3, s4, '0010')
        s6 = add_gate_from_tt(circuit, x2, s5, '0001')
        s7 = add_gate_from_tt(circuit, x2, s5, '0111')
        s8 = add_gate_from_tt(circuit, s4, s6, '0111')
        s9 = add_gate_from_tt(circuit, s6, s7, '1011')
        return [s9, s8]
    else:
        raise BadBasisError(f"Unsupported basis: {basis}")


def add_sub_two_numbers(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> list[gate.Label]:
    """
    Function to subtract two binary numbers represented by input labels.

    :param circuit: The general circuit.
    :param input_labels_a: List of bits representing the first binary number.
    :param input_labels_b: List of bits representing the second binary number.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: List of bits representing the difference of the two numbers.

    """
    _input_labels_a = list(input_labels_a)
    _input_labels_b = list(input_labels_b)
    n = len(_input_labels_a)
    m = len(_input_labels_b)

    if big_endian:
        _input_labels_a.reverse()
        _input_labels_b.reverse()

    res = [PLACEHOLDER_STR] * n
    bal = [PLACEHOLDER_STR] * n
    res[0], bal[0] = add_sub2(
        circuit, [_input_labels_a[0], _input_labels_b[0]], basis=basis
    )
    for i in range(1, n):
        if i < m:
            res[i], bal[i] = add_sub3(
                circuit,
                [_input_labels_a[i], _input_labels_b[i], bal[i - 1]],
                basis=basis,
            )
        else:
            res[i], bal[i] = add_sub2(
                circuit, [_input_labels_a[i], bal[i - 1]], basis=basis
            )

    return reverse_if_big_endian(res, big_endian)


def add_subtract_with_compare(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    big_endian: bool = False,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> tuple[list[gate.Label], gate.Label]:
    """
    Subtracts given integer b from integer a and return residual bit representing if
    subtraction was successful (equivalent to a>=b).

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: tuple (labels that carry subtraction result, label of gate that carries
        residual bit)

    """
    _input_labels_a: list[str] = list(input_labels_a)
    _input_labels_b: list[str] = list(input_labels_b)

    if big_endian:
        _input_labels_a.reverse()
        _input_labels_b.reverse()

    always_false = add_gate_from_tt(
        circuit, _input_labels_a[0], _input_labels_b[0], "0000"
    )
    while len(_input_labels_a) < len(_input_labels_b):
        _input_labels_a.append(always_false)
    while len(_input_labels_a) > len(_input_labels_b):
        _input_labels_b.append(always_false)

    validate_equal_sizes(_input_labels_a, _input_labels_b)

    n = len(_input_labels_a)

    res = [PLACEHOLDER_STR] * n
    bal = [PLACEHOLDER_STR] * n

    res[0], bal[0] = add_sub2(
        circuit,
        [_input_labels_a[0], _input_labels_b[0]],
        basis=basis,
    )
    for i in range(1, n):
        res[i], bal[i] = add_sub3(
            circuit,
            [_input_labels_a[i], _input_labels_b[i], bal[i - 1]],
            basis=basis,
        )
    return reverse_if_big_endian(res, big_endian), bal[n - 1]


def _kogge_stone_borrow_lookahead(
    circuit: Circuit,
    a: list[gate.Label],
    b: list[gate.Label],
    zero: gate.Label,
    *,
    basis: GenerationBasis = GenerationBasis.XAIG,
) -> tuple[list[gate.Label], gate.Label]:
    n = len(a)

    difference_, borrow_gen_, borrow_prop_ = zip(
        *[
            (
                xor_two_bits(circuit, a[i], b[i], basis=basis),
                add_gate_from_tt(circuit, a[i], b[i], '0100'),
                add_gate_from_tt(circuit, a[i], b[i], '1001'),
            )
            for i in range(n)
        ]
    )
    difference: list[gate.Label] = list(difference_)
    borrow_gen: list[gate.Label] = list(borrow_gen_)
    borrow_prop: list[gate.Label] = list(borrow_prop_)

    stride = 1
    while stride < n:
        for i in range(n - 1, stride - 1, -1):
            t = add_gate_from_tt(
                circuit, borrow_prop[i], borrow_gen[i - stride], '0001'
            )
            borrow_gen[i] = add_gate_from_tt(circuit, borrow_gen[i], t, '0111')
        for i in range(n - 1, stride - 1, -1):
            borrow_prop[i] = add_gate_from_tt(
                circuit, borrow_prop[i], borrow_prop[i - stride], '0001'
            )
        stride *= 2

    borrow_into = [zero] + borrow_gen
    result = [
        xor_two_bits(circuit, difference[i], borrow_into[i], basis=basis)
        for i in range(n)
    ]

    return result, borrow_gen[n - 1]


def add_sub_two_numbers_log_depth(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    basis: GenerationBasis = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> list[gate.Label]:
    """
    Subtract two binary numbers in O(log n) depth using a Kogge-Stone borrow-lookahead
    network.

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :return: Bits representing (a - b) mod 2^n, where n = len(a).

    """
    a = list(input_labels_a)
    b = list(input_labels_b)
    n = len(a)
    if big_endian:
        a.reverse()
        b.reverse()

    zero = add_gate_from_tt(circuit, a[0], a[0], '0000')

    b = b[:n]
    while len(b) < n:
        b.append(zero)

    result, _ = _kogge_stone_borrow_lookahead(circuit, a, b, zero, basis=basis)

    return reverse_if_big_endian(result, big_endian)


def add_subtract_with_compare_log_depth(
    circuit: Circuit,
    input_labels_a: tp.Iterable[gate.Label],
    input_labels_b: tp.Iterable[gate.Label],
    *,
    basis: GenerationBasis = GenerationBasis.XAIG,
    big_endian: bool = False,
) -> tuple[list[gate.Label], gate.Label]:
    """
    Subtract b from a in O(log n) depth and return a residual borrow bit indicating
    whether a < b (Kogge-Stone borrow-lookahead).

    :param circuit: The general circuit.
    :param input_labels_a: labels representing integer a.
    :param input_labels_b: labels representing integer b.
    :param basis: in which basis should generated function lie. Supported [XAIG, AIG].
    :param big_endian: defines how to interpret numbers, big-endian or little-endian
        format
    :return: (result labels, borrow bit). Borrow is 0 when a >= b, 1 when a < b.

    """
    a = list(input_labels_a)
    b = list(input_labels_b)

    if big_endian:
        a.reverse()
        b.reverse()

    always_false = add_gate_from_tt(circuit, a[0], b[0], '0000')
    while len(a) < len(b):
        a.append(always_false)
    while len(a) > len(b):
        b.append(always_false)

    validate_equal_sizes(a, b)

    result, borrow_out = _kogge_stone_borrow_lookahead(
        circuit, a, b, always_false, basis=basis
    )

    return reverse_if_big_endian(result, big_endian), borrow_out
