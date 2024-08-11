import itertools
import typing as tp

import pytest

from boolean_circuit_tool.core.boolean_function import RawTruthTable, RawTruthTableModel
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.logic import DontCare, TriValue
from boolean_circuit_tool.core.truth_table import _parse_trival, TruthTableModel
from boolean_circuit_tool.synthesis.circuit_search import (
    _tt_to_gate_type,
    Basis,
    CircuitFinderSat,
    Operation,
)
from boolean_circuit_tool.synthesis.exception import (
    FixGateError,
    FixGateOrderError,
    ForbidWireOrderError,
    GateIsAbsentError,
    NoSolutionError,
    SolverTimeOutError,
)
from pysat.solvers import Solver


def check_exact_circuit_size(size, truth_tables, basis, hasdontcares=False):
    circuit = CircuitFinderSat(
        TruthTableModel(truth_tables), size, basis=basis
    ).find_circuit()
    check_correctness(circuit, truth_tables, hasdontcares)
    with pytest.raises(NoSolutionError):
        CircuitFinderSat(
            TruthTableModel(truth_tables), size - 1, basis=basis
        ).find_circuit()


def check_is_suitable_truth_table(tt: RawTruthTable, pattern_tt: RawTruthTableModel):
    def _is_suitable_one_output_truth_table(
        one_out_tt: tp.Sequence[bool],
        one_out_pattern_tt: tp.MutableSequence[TriValue],
    ):
        return all(
            y == DontCare or x == y for x, y in zip(one_out_tt, one_out_pattern_tt)
        )

    assert len(tt) == len(pattern_tt)
    assert all(
        [_is_suitable_one_output_truth_table(a, b) for a, b in zip(tt, pattern_tt)]
    )


def check_correctness(
    circuit: Circuit,
    truth_tables: tp.Sequence[tp.Sequence[str]],
    hasdontcares: bool = False,
):
    assert isinstance(circuit, Circuit)
    truth_tables_bool = [
        list(map(_parse_trival, output_tt)) for output_tt in truth_tables
    ]
    if hasdontcares:
        check_is_suitable_truth_table(circuit.get_truth_table(), truth_tables_bool)
    else:
        assert circuit.get_truth_table() == truth_tables_bool


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
    circuit = CircuitFinderSat(
        TruthTableModel(tt), size, basis=Basis.XAIG
    ).find_circuit()
    check_correctness(circuit, tt)


@pytest.mark.parametrize("inputs, outputs, size", [(2, 2, 2), (3, 2, 5), (4, 3, 9)])
def test_sum_with_precomputed_xor(inputs: int, outputs: int, size: int):
    tt = [
        ''.join(
            str((sum(x) >> i) & 1) for x in itertools.product(range(2), repeat=inputs)
        )
        for i in range(outputs)
    ]
    circuit_finder = CircuitFinderSat(TruthTableModel(tt), size, basis=Basis.XAIG)
    circuit_finder.fix_gate(gate=inputs,
                            first_predecessor=0,
                            second_predecessor=1,
                            gate_type=_tt_to_gate_type[(0, 1, 1, 0)]
                            )
    for k in range(inputs - 2):
        circuit_finder.fix_gate(
            gate=inputs + k + 1,
            first_predecessor=k + 2,
            second_predecessor=inputs + k,
            gate_type=_tt_to_gate_type[(0, 1, 1, 0)]
        )
    circuit = circuit_finder.find_circuit()
    check_correctness(circuit, tt)

    def add_s(gate_n):
        if gate_n >= inputs:
            return f"s{gate_n}"
        return str(gate_n)

    gate = circuit.get_gate(f"s{inputs}")
    assert gate.gate_type == _tt_to_gate_type[(0, 1, 1, 0)]
    assert gate.operands == ('0', '1')
    for k in range(inputs - 2):
        gate = circuit.get_gate(add_s(inputs + k + 1))
        assert gate.gate_type == _tt_to_gate_type[(0, 1, 1, 0)]
        assert gate.operands == (add_s(k + 2), add_s(inputs + k))


@pytest.mark.parametrize("inputs, size", [(3, 6), (4, 9)])
def test_aig_basis(inputs: int, size: int):
    tt = [''.join(str(sum(x) % 2) for x in itertools.product(range(2), repeat=inputs))]
    circuit = CircuitFinderSat(
        TruthTableModel(tt), size, basis=Basis.AIG
    ).find_circuit()
    check_correctness(circuit, tt)


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
    with pytest.raises(SolverTimeOutError):
        CircuitFinderSat(TruthTableModel(tt), size, basis=Basis.XAIG).find_circuit(
            time_limit=tl
        )


def test_simple_dont_care():
    tt = ["011*"]
    check_exact_circuit_size(1, tt, [Operation.or_], hasdontcares=True)


@pytest.mark.parametrize("tt, size, sat", [(["0110"], 3, True), (["0110"], 2, False)])
def test_get_cnf(tt, size, sat):
    circuit_finder = CircuitFinderSat(TruthTableModel(tt), size, basis=Basis.AIG)
    cnf = circuit_finder.get_cnf()
    print(cnf)

    solver = Solver(name='g3')
    for clause in cnf:
        solver.add_clause(clause)
    is_sat = solver.solve()
    assert is_sat == sat
    solver.delete()


def test_need_normalized():
    tt = ['00010001', '11110101', '11111010']
    tt_normalized = ['00010001', '00001010', '00000101']

    circuit = CircuitFinderSat(
        TruthTableModel(tt), 3, basis=Basis.XAIG, need_normalized=False
    ).find_circuit()
    check_correctness(circuit, tt)

    with pytest.raises(NoSolutionError):
        CircuitFinderSat(
            TruthTableModel(tt), 10, basis=Basis.FULL, need_normalized=True
        ).find_circuit()

    circuit = CircuitFinderSat(
        TruthTableModel(tt_normalized), 3, basis=Basis.XAIG, need_normalized=True
    ).find_circuit()
    check_correctness(circuit, tt_normalized)


def test_fix_gate_exceptions():
    tt = ["01101001"]
    circuit_finder = CircuitFinderSat(TruthTableModel(tt), 6, basis=Basis.AIG)
    with pytest.raises(GateIsAbsentError):
        circuit_finder.fix_gate(gate=9, first_predecessor=0, second_predecessor=2)
    with pytest.raises(GateIsAbsentError):
        circuit_finder.fix_gate(gate=8, first_predecessor=0, second_predecessor=9)
    with pytest.raises(GateIsAbsentError):
        circuit_finder.fix_gate(gate=8, first_predecessor=9, second_predecessor=6)
    with pytest.raises(FixGateError):
        circuit_finder.fix_gate(gate=3)
    with pytest.raises(FixGateOrderError):
        circuit_finder.fix_gate(gate=3, first_predecessor=2, second_predecessor=1)
    with pytest.raises(FixGateOrderError):
        circuit_finder.fix_gate(gate=3, first_predecessor=4)

    circuit_finder.fix_gate(gate=4, first_predecessor=1)
    ckt = circuit_finder.find_circuit()
    check_correctness(ckt, tt)
    assert '1' in ckt.get_gate('s4').operands


def test_forbid_wire_exceptions():
    tt = ["01101001"]
    circuit_finder = CircuitFinderSat(TruthTableModel(tt), 6, basis=Basis.AIG)
    with pytest.raises(GateIsAbsentError):
        circuit_finder.forbid_wire(9, 0)
    with pytest.raises(GateIsAbsentError):
        circuit_finder.forbid_wire(0, 9)
    with pytest.raises(ForbidWireOrderError):
        circuit_finder.forbid_wire(5, 3)
    circuit_finder.forbid_wire(1, 3)
    ckt = circuit_finder.find_circuit()
    check_correctness(ckt, tt)
    assert '1' not in ckt.get_gate('s3').operands


def test_fix_forbid():
    tt = ["01101001"]
    circuit_finder = CircuitFinderSat(TruthTableModel(tt), 6, basis=Basis.AIG)
    circuit_finder.fix_gate(gate=4, first_predecessor=1)
    circuit_finder.forbid_wire(1, 4)
    with pytest.raises(NoSolutionError):
        circuit_finder.find_circuit()
