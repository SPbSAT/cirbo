import typing as tp

import pytest
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.sat import (
    is_circuit_satisfiable,
    is_satisfiable,
    PySATSolverNames,
)
from boolean_circuit_tool.sat.cnf import Cnf, CnfRaw

from tests.boolean_circuit_tool.sat.cnf.generator_utils import (
    generate_circuit1,
    generate_circuit2,
    generate_circuit3,
    generate_circuit4,
)


@pytest.mark.parametrize(
    'cnf, expected_answer, expected_model',
    [
        (Cnf([[-1, -2], [-1, 3], [1]]), True, [1, -2, 3]),
        (Cnf([[1], [-1]]), False, None),
    ],
)
@pytest.mark.parametrize(
    'solver_name',
    [
        'cadical195',
        PySATSolverNames.GLUCOSE4,
    ],
)
def test_is_satisfiable(
    cnf: Cnf,
    solver_name: tp.Union[PySATSolverNames, str],
    expected_answer: bool,
    expected_model: tp.Optional[list[int]],
):
    sat_result = is_satisfiable(cnf, solver_name=solver_name)
    assert sat_result.answer == expected_answer
    assert sat_result.model == expected_model


@pytest.mark.parametrize(
    'generate_circuit, expected_answer, expected_model',
    [
        (generate_circuit1, True, [1, 2, 3]),
        (generate_circuit2, True, [-1, -2, -3, 4, 5, 6]),
        (generate_circuit3, True, [1, 2, 3, -4, 5, -6, 7]),
        (generate_circuit4, False, None),
    ],
)
@pytest.mark.parametrize(
    'solver_name',
    [
        'cadical195',
        PySATSolverNames.GLUCOSE4,
    ],
)
def test_is_circuit_satisfiable(
    generate_circuit: tp.Callable[[], tp.Tuple[Circuit, CnfRaw]],
    solver_name: tp.Union[PySATSolverNames, str],
    expected_answer: bool,
    expected_model: tp.Optional[list[int]],
):
    circuit, _ = generate_circuit()
    sat_result = is_circuit_satisfiable(circuit, solver_name=solver_name)
    assert sat_result.answer == expected_answer
    assert sat_result.model == expected_model
