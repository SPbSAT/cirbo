import itertools
import typing as tp

import pytest

from boolean_circuit_tool.core.boolean_function import RawTruthTable, RawTruthTableModel
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.logic import DontCare, TriValue
from boolean_circuit_tool.core.truth_table import TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import (
    _tt_to_gate_type,
    Basis,
    CircuitFinder,
    get_tt_by_str,
    Operation,
)
from boolean_circuit_tool.synthesis.exception import SolverTimeOutError


def check_exact_circuit_size(size, truth_tables, basis, hasdontcares=False):
    truth_tables_bool = get_tt_by_str(truth_tables)
    circuit_finder = CircuitFinder(TruthTableModel(truth_tables_bool), size, basis)
    circuit = circuit_finder.solve_cnf()
    check_correctness(circuit, truth_tables_bool, hasdontcares)
    assert (
        CircuitFinder(TruthTableModel(truth_tables_bool), size - 1, basis).solve_cnf()
        is False
    )


def check_is_suitable_truth_table(tt: RawTruthTable, pattern_tt: RawTruthTableModel):
    def _is_suitable_one_output_truth_table(
        one_out_tt: tp.MutableSequence[bool],
        one_out_pattern_tt: tp.MutableSequence[TriValue],
    ):
        return all(
            isinstance(y, type(DontCare)) or x == y
            for x, y in zip(one_out_tt, one_out_pattern_tt)
        )

    assert len(tt) == len(pattern_tt)
    assert all(
        [_is_suitable_one_output_truth_table(a, b) for a, b in zip(tt, pattern_tt)]
    )


def check_correctness(
    circuit: tp.Union[Circuit, bool],
    truth_table: RawTruthTableModel,
    hasdontcares: bool = False,
):
    assert isinstance(circuit, Circuit)
    if hasdontcares:
        check_is_suitable_truth_table(circuit.get_truth_table(), truth_table)
    else:
        assert circuit.get_truth_table() == truth_table


def test_small_xors():
    for n in range(2, 7):
        tt = [''.join(str(sum(x) % 2) for x in itertools.product(range(2), repeat=n))]
        check_exact_circuit_size(n - 1, tt, Basis.XAIG)


def test_and_ors():
    for n in range(2, 5):
        tt = [
            ''.join(
                ('1' if all(x[i] == 1 for i in range(n)) else '0')
                for x in itertools.product(range(2), repeat=n)
            ),
            ''.join(
                ('1' if any(x[i] == 1 for i in range(n)) else '0')
                for x in itertools.product(range(2), repeat=n)
            ),
        ]
        check_exact_circuit_size(2 * n - 2, tt, Basis.XAIG)


@pytest.mark.parametrize("inputs", [2, 3, 4])
def test_all_equal(inputs: int):
    tt = [
        ''.join(
            '1' if all(x[i] == x[i + 1] for i in range(inputs - 1)) else '0'
            for x in itertools.product(range(2), repeat=inputs)
        )
    ]
    check_exact_circuit_size(2 * inputs - 3, tt, Basis.XAIG)


@pytest.mark.parametrize("inputs, outputs, size", [(2, 2, 2), (3, 2, 5), (4, 3, 9)])
def test_sum_circuits(inputs: int, outputs: int, size: int):
    tt = [
        ''.join(
            str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=inputs)
        )
        for i in range(outputs)
    ]
    truth_tables_bool = get_tt_by_str(tt)
    circuit = CircuitFinder(
        TruthTableModel(truth_tables_bool), size, Basis.XAIG
    ).solve_cnf()
    check_correctness(circuit, truth_tables_bool)


@pytest.mark.parametrize("inputs, outputs, size", [(2, 2, 2), (3, 2, 5), (4, 3, 9)])
def test_sum_with_precomputed_xor(inputs: int, outputs: int, size: int):
    tt = [
        ''.join(
            str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=inputs)
        )
        for i in range(outputs)
    ]
    truth_tables_bool = get_tt_by_str(tt)
    circuit_finder = CircuitFinder(TruthTableModel(truth_tables_bool), size, Basis.XAIG)
    circuit_finder.fix_gate(inputs, 0, 1, _tt_to_gate_type[(0, 1, 1, 0)])
    for k in range(inputs - 2):
        circuit_finder.fix_gate(
            inputs + k + 1, k + 2, inputs + k, _tt_to_gate_type[(0, 1, 1, 0)]
        )
    circuit = circuit_finder.solve_cnf()
    check_correctness(circuit, truth_tables_bool)


@pytest.mark.parametrize("inputs, size", [(3, 6), (4, 9)])
def test_aig_basis(inputs: int, size: int):
    tt = [''.join(str(sum(x) % 2) for x in itertools.product(range(2), repeat=inputs))]

    truth_tables_bool = get_tt_by_str(tt)
    circuit = CircuitFinder(
        TruthTableModel(truth_tables_bool), size, Basis.AIG
    ).solve_cnf()
    check_correctness(circuit, truth_tables_bool)


def test_simple_operations():
    tt = [op.value for op in Operation][:10]
    check_exact_circuit_size(10, tt, Basis.FULL)
    tt = [op.value for op in Operation][10:]
    check_exact_circuit_size(6, tt, Basis.FULL)


@pytest.mark.parametrize("inputs, outputs, size, tl", [(5, 3, 11, 1)])
def test_time_limit(inputs: int, outputs: int, size: int, tl: int):
    tt = [
        ''.join(
            str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=inputs)
        )
        for i in range(outputs)
    ]

    truth_tables_bool = get_tt_by_str(tt)
    finder = CircuitFinder(TruthTableModel(truth_tables_bool), size, Basis.XAIG)
    with pytest.raises(SolverTimeOutError):
        finder.solve_cnf(time_limit=tl)


def test_simple_dont_care():
    tt = ["011*"]
    check_exact_circuit_size(1, tt, [Operation.or_], hasdontcares=True)
