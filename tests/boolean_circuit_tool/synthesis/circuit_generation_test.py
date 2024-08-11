import pytest

from boolean_circuit_tool.core.utils import canonical_index_to_input
from boolean_circuit_tool.synthesis.generation import (
    generate_if_then_else,
    generate_pairwise_if_then_else,
    generate_pairwise_xor,
    generate_plus_one,
)


def to_list_of_bool(n, bit_len):
    bit_str = "{0:b}".format(n).zfill(bit_len)
    res = []
    bit_str_len = len(bit_str)
    for i in range(bit_str_len - 1, bit_str_len - bit_len - 1, -1):
        res.append(bool(int(bit_str[i])))
    return res


@pytest.mark.parametrize("n", range(1, 10))
@pytest.mark.parametrize("m", range(1, 20))
def test_generate_plus_one(n: int, m: int):
    circuit = generate_plus_one(n, m)
    for i in range(2**n):
        inp = to_list_of_bool(i, n)
        out = to_list_of_bool(i + 1, m)

        test_out = circuit.evaluate(inp)
        assert test_out == out


@pytest.mark.parametrize("if_inp", [True, False])
@pytest.mark.parametrize("then_inp", [True, False])
@pytest.mark.parametrize("else_inp", [True, False])
def test_generate_if_then_else(if_inp: bool, then_inp: bool, else_inp: bool):
    circuit = generate_if_then_else()
    if if_inp:
        real_res = then_inp
    else:
        real_res = else_inp
    test_res = circuit.evaluate([if_inp, then_inp, else_inp])[0]
    assert test_res == real_res


@pytest.mark.parametrize("n", range(1, 5))
def test_generate_pairwise_if_then_else(n: int):
    all_bit_strings = [canonical_index_to_input(i, n) for i in range(2**n)]
    circuit = generate_pairwise_if_then_else(n)
    for if_inp in all_bit_strings:
        for then_inp in all_bit_strings:
            for else_inp in all_bit_strings:
                real_res = []
                for i in range(n):
                    if if_inp[i]:
                        real_res.append(then_inp[i])
                    else:
                        real_res.append(else_inp[i])
                test_out = circuit.evaluate(
                    list(if_inp) + list(then_inp) + list(else_inp)
                )
                assert test_out == real_res


@pytest.mark.parametrize("n", range(1, 5))
def test_generate_pairwise_xor(n: int):
    all_bit_strings = [canonical_index_to_input(i, n) for i in range(2**n)]
    circuit = generate_pairwise_xor(n)

    for x in all_bit_strings:
        for y in all_bit_strings:
            test_out = circuit.evaluate(list(x) + list(y))
            real_res = [x[i] ^ y[i] for i in range(n)]
            assert test_out == real_res
