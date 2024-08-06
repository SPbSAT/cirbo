import pytest
import typing as tp

from tests.boolean_circuit_tool.cnf.tseytin_test import (
    generate_circuit1,
    generate_circuit2,
    generate_circuit3,
    generate_circuit4,
)
from boolean_circuit_tool.cnf import CnfRaw
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import is_satisfiable


@pytest.mark.parametrize(
    'generate_circuit, is_sat',
    [
        (generate_circuit1, True),
        (generate_circuit2, True),
        (generate_circuit3, True),
        (generate_circuit4, True),
    ],
)
def test_is_satisfiable(
        generate_circuit: tp.Callable[[], tp.Tuple[Circuit, CnfRaw]], is_sat: bool
):
    circuit, _ = generate_circuit()
    assert is_satisfiable(circuit) == is_sat
