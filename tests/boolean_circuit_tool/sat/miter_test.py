from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat.miter import build_miter
from boolean_circuit_tool.synthesis.generation import generate_inputs, generate_plus_one


def to_list_of_bool(n, bit_len):
    bit_str = "{0:b}".format(n).zfill(bit_len)
    res = []
    bit_str_len = len(bit_str)
    for i in range(bit_str_len - 1, bit_str_len - bit_len - 1, -1):
        res.append(bool(int(bit_str[i])))
    return res


def test_miter():
    for n in range(2, 10):
        plus_zero = generate_inputs(n)
        plus_one = generate_plus_one(inp_len=n, out_len=n)
        plus_two = (
            Circuit()
            .add_circuit(plus_one, name='first')
            .extend_circuit(plus_one, name='second')
        )
        plus_three = (
            Circuit().add_circuit(plus_two).extend_circuit(plus_one, name='third')
        )

        circuits = [plus_zero, plus_one, plus_two, plus_three]
        for c1 in circuits:
            for c2 in circuits:
                miter = build_miter(c1, c2)
                sat_miter = False
                for i in range(2**n):
                    sat_miter = sat_miter or miter.evaluate(to_list_of_bool(i, n))[0]
                if c1 == c2:
                    assert sat_miter == False
                else:
                    assert sat_miter == True
