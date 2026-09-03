import typing as tp

import pytest
from cirbo.core.circuit import Circuit, Gate, gate
from cirbo.sat import (
    check_circuits_equivalence,
    is_circuit_satisfiable,
    is_satisfiable,
    PySATSolverNames,
)
from cirbo.sat.cnf import Cnf, CnfRaw

from tests.cirbo.sat.cnf.generator_utils import (
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


def test_check_circuits_equivalence():
    left = Circuit.bare_circuit(2)
    left.add_gate(Gate('out', gate.AND, ('0', '1')))
    left.mark_as_output('out')

    equivalent = Circuit.bare_circuit(2)
    equivalent.add_gate(Gate('and_1', gate.AND, ('0', '1')))
    equivalent.add_gate(Gate('and_2', gate.AND, ('0', '1')))
    equivalent.add_gate(Gate('out', gate.OR, ('and_1', 'and_2')))
    equivalent.mark_as_output('out')

    different = Circuit.bare_circuit(2)
    different.add_gate(Gate('out', gate.OR, ('0', '1')))
    different.mark_as_output('out')

    different_shape = Circuit.bare_circuit(1)
    different_shape.mark_as_output('0')

    assert check_circuits_equivalence(left, equivalent)
    assert not check_circuits_equivalence(left, different)
    assert not check_circuits_equivalence(left, different_shape)
