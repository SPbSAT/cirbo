import itertools
import typing as tp

import pytest

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.truth_table import TruthTable
from boolean_circuit_tool.synthesis.circuit_search import (
    _tt_to_gate_type,
    Basis,
    CircuitFinder,
    Operation,
)
from boolean_circuit_tool.synthesis.exception import SolverTimeOutError


def check_exact_circuit_size(n, size, truth_tables, basis):
    truth_tables_bool = [[bool(int(el)) for el in x] for x in truth_tables]
    circuit_finder = CircuitFinder(TruthTable(truth_tables_bool), size, basis)
    circuit = circuit_finder.solve_cnf()
    check_correctness(circuit, truth_tables_bool)
    assert (
        CircuitFinder(TruthTable(truth_tables_bool), size - 1, basis).solve_cnf()
        is False
    )


def check_correctness(
    circuit: tp.Union[Circuit, bool], truth_table: tp.List[tp.List[bool]]
):
    assert isinstance(circuit, Circuit)
    assert circuit.get_truth_table() == truth_table


def test_small_xors():
    for n in range(2, 7):
        tt = [''.join(str(sum(x) % 2) for x in itertools.product(range(2), repeat=n))]
        check_exact_circuit_size(n, n - 1, tt, Basis.XAIG)


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
        check_exact_circuit_size(n, 2 * n - 2, tt, Basis.XAIG)


def test_all_equal():
    for n in range(2, 5):
        tt = [
            ''.join(
                '1' if all(x[i] == x[i + 1] for i in range(n - 1)) else '0'
                for x in itertools.product(range(2), repeat=n)
            )
        ]
        check_exact_circuit_size(n, 2 * n - 3, tt, Basis.XAIG)


def test_sum_circuits():
    for n, l, size in ((2, 2, 2), (3, 2, 5), (4, 3, 9)):
        tt = [
            ''.join(
                str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=n)
            )
            for i in range(l)
        ]
        truth_tables_bool = [[bool(int(el)) for el in x] for x in tt]
        circuit = CircuitFinder(
            TruthTable(truth_tables_bool), size, Basis.XAIG
        ).solve_cnf()
        check_correctness(circuit, truth_tables_bool)


def test_sum_with_precomputed_xor():
    for n, l, size in ((2, 2, 2), (3, 2, 5), (4, 3, 9)):
        tt = [
            ''.join(
                str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=n)
            )
            for i in range(l)
        ]
        truth_tables_bool = [[bool(int(el)) for el in x] for x in tt]
        circuit_finder = CircuitFinder(TruthTable(truth_tables_bool), size, Basis.XAIG)
        circuit_finder.fix_gate(n, 0, 1, _tt_to_gate_type[(0, 1, 1, 0)])
        for k in range(n - 2):
            circuit_finder.fix_gate(
                n + k + 1, k + 2, n + k, _tt_to_gate_type[(0, 1, 1, 0)]
            )
        circuit = circuit_finder.solve_cnf()
        check_correctness(circuit, truth_tables_bool)


def test_aig_basis():
    for n, size in ((3, 6), (4, 9)):
        tt = [''.join(str(sum(x) % 2) for x in itertools.product(range(2), repeat=n))]

        truth_tables_bool = [[bool(int(el)) for el in x] for x in tt]
        circuit = CircuitFinder(
            TruthTable(truth_tables_bool), size, Basis.AIG
        ).solve_cnf()
        check_correctness(circuit, truth_tables_bool)


def test_simple_operations():
    tt = [op.value for op in Operation][:10]
    check_exact_circuit_size(2, 10, tt, Basis.FULL)
    tt = [op.value for op in Operation][10:]
    check_exact_circuit_size(2, 6, tt, Basis.FULL)


def test_time_limit():
    n, outs = 5, 3
    truth_tables = [
        ''.join(str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=n))
        for i in range(outs)
    ]

    truth_tables_bool = [[bool(int(el)) for el in x] for x in truth_tables]
    size = 12
    finder = CircuitFinder(TruthTable(truth_tables_bool), size, Basis.XAIG)
    with pytest.raises(SolverTimeOutError):
        finder.solve_cnf(time_limit=1)
