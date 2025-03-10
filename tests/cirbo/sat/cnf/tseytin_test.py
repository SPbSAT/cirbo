import typing as tp

import pytest

from cirbo.core.circuit import Circuit
from cirbo.sat.cnf import Cnf, CnfRaw

from tests.cirbo.sat.cnf.generator_utils import (
    generate_circuit1,
    generate_circuit2,
    generate_circuit3,
    generate_circuit4,
)


@pytest.mark.parametrize(
    'generate_circuit',
    [
        generate_circuit1,
        generate_circuit2,
        generate_circuit3,
        generate_circuit4,
    ],
)
def test_tseytin(generate_circuit: tp.Callable[[], tp.Tuple[Circuit, CnfRaw]]):
    circuit, expected_cnf = generate_circuit()
    cnf = Cnf.from_circuit(circuit).get_raw()
    assert cnf == expected_cnf
