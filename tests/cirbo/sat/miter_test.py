import pytest

from cirbo.core.circuit import Circuit
from cirbo.sat import is_circuit_satisfiable
from cirbo.sat.miter import build_miter
from cirbo.synthesis.generation.generation import generate_plus_one


@pytest.mark.parametrize("n", range(2, 9))
def test_miter(n: int):
    plus_zero = Circuit.bare_circuit(n, prefix='x', set_as_outputs=True)
    plus_one = generate_plus_one(inp_len=n, out_len=n)
    plus_two = (
        Circuit()
        .add_circuit(plus_one, name='first')
        .extend_circuit(plus_one, name='second')
    )
    plus_three = Circuit().add_circuit(plus_two).extend_circuit(plus_one, name='third')

    circuits = [plus_zero, plus_one, plus_two, plus_three]
    for c1 in circuits:
        for c2 in circuits:
            miter = build_miter(c1, c2)
            assert is_circuit_satisfiable(miter).answer == (c1 != c2)
