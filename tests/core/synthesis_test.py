from itertools import product
from typing import List
from boolean_circuit_tool.core.circuit import Circuit, GateState
from boolean_circuit_tool.core.synthesis.circuit_search import (
    CircuitFinder,
    Function,
    Operation,
)


def get_tt(circuit: Circuit) -> List[GateState]:
    n = len(circuit.inputs)
    truth_table = []
    for inp in product([0, 1], repeat=n):
        b = circuit.evaluate_circuit({str(i): inp[i] for i in range(n)})
        truth_table.append(b)
    return truth_table


my_basis = [
    Operation.NOT,
    Operation.AND,
    Operation.OR,
    Operation.NAND,
    Operation.NOR,
    Operation.XOR,
    Operation.NXOR,
]


def check_exact_circuit_size(n, size, truth_tables, basis):
    circuit_finder = CircuitFinder(Function(truth_tables), size, basis)
    circuit = circuit_finder.solve_cnf()
    assert circuit is not None
    circuit_truth_tables = ''.join([str(int(i)) for i in get_tt(circuit)])
    assert truth_tables[0] == circuit_truth_tables
    assert CircuitFinder(Function(truth_tables), size - 1, basis).solve_cnf() is False


def test_small_xors():
    for n in range(2, 7):
        tt = [''.join(str(sum(x) % 2) for x in product(range(2), repeat=n))]
        check_exact_circuit_size(n, n - 1, tt, my_basis)


def test_and_ors():
    for n in range(2, 5):
        tt = [
            ''.join(
                ('1' if all(x[i] == 1 for i in range(n)) else '0')
                for x in product(range(2), repeat=n)
            ),
            ''.join(
                ('1' if any(x[i] == 1 for i in range(n)) else '0')
                for x in product(range(2), repeat=n)
            ),
        ]
        check_exact_circuit_size(n, 2 * n - 2, tt, my_basis)


def test_all_equal():
    for n in range(2, 5):
        tt = [
            ''.join(
                '1' if all(x[i] == x[i + 1] for i in range(n - 1)) else '0'
                for x in product(range(2), repeat=n)
            )
        ]
        check_exact_circuit_size(n, 2 * n - 3, tt, my_basis)
