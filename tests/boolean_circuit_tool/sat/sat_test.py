import typing as tp

import pytest
from boolean_circuit_tool.cnf import CnfRaw
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import is_satisfiable

from tests.boolean_circuit_tool.cnf.tseytin_test import (
    generate_circuit1,
    generate_circuit2,
    generate_circuit3,
    generate_circuit4,
)


@pytest.mark.parametrize(
    'generate_circuit, is_sat, model',
    [
        (generate_circuit1, True, [1, 2, 3]),
        (generate_circuit2, True, [-1, -2, -3, 4, 5, 6]),
        (generate_circuit3, True, [1, 2, 3, -4, 5, -6, 7]),
        (generate_circuit4, False, None),
    ],
)
def test_is_satisfiable(
    generate_circuit: tp.Callable[[], tp.Tuple[Circuit, CnfRaw]],
    is_sat: bool,
    model: tp.Optional[list[int]],
):
    circuit, _ = generate_circuit()
    sat_result = is_satisfiable(circuit)
    assert sat_result.answer == is_sat
    assert sat_result.model == model
