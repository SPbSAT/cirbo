import functools
import itertools

import pytest

from cirbo.core.circuit import Circuit, gate
from cirbo.core.circuit.gate import Label
from cirbo.core.truth_table import TruthTable
from cirbo.synthesis.generation import generate_circuit_pm1971


def _output_depths(circuit: Circuit) -> list[int]:
    @functools.lru_cache(maxsize=None)
    def gate_depth(label: Label) -> int:
        current_gate = circuit.gates[label]
        if current_gate.gate_type in {
            gate.INPUT,
            gate.ALWAYS_FALSE,
            gate.ALWAYS_TRUE,
        }:
            return 0
        if current_gate.gate_type == gate.NOT:
            return gate_depth(current_gate.operands[0])
        return 1 + max(map(gate_depth, current_gate.operands))

    return [gate_depth(output) for output in circuit.outputs]


@pytest.mark.parametrize("input_size", range(5))
def test_all_single_minterm_functions(input_size: int):
    table_size = 1 << input_size
    errors = []
    for true_index in range(table_size):
        truth_table = [index == true_index for index in range(table_size)]
        function = TruthTable([truth_table])
        circuit = generate_circuit_pm1971(function)

        actual = circuit.get_truth_table()
        expected = function.get_truth_table()
        if actual != expected:
            errors.append((true_index, actual, expected))

    assert not errors


@pytest.mark.parametrize("input_size", range(1, 7))
def test_dense_and_sparse_functions(input_size: int):
    table_size = 1 << input_size
    rows = [
        [index % 2 == 0 for index in range(table_size)],
        [bin(index).count("1") % 2 == 1 for index in range(table_size)],
        [index not in {1, table_size - 1} for index in range(table_size)],
    ]
    function = TruthTable(rows)
    circuit = generate_circuit_pm1971(function)

    assert circuit.get_truth_table() == function.get_truth_table()
    assert max(_output_depths(circuit)) <= input_size + 1


@pytest.mark.parametrize("input_size", range(3, 9))
def test_reaches_n_plus_one_depth_bound(input_size: int):
    truth_table = [bin(index).count("1") % 2 == 1 for index in range(1 << input_size)]
    circuit = generate_circuit_pm1971(TruthTable([truth_table]))

    assert circuit.get_truth_table() == [truth_table]
    assert _output_depths(circuit) == [input_size + 1]


def test_depth_bound_for_21_inputs_and_five_variable_parity():
    input_size = 21
    prefix_size = 16
    truth_table = [
        bin(index >> prefix_size).count("1") % 2 == 1
        for index in range(1 << input_size)
    ]

    circuit = generate_circuit_pm1971(TruthTable([truth_table]))

    assert all(depth <= input_size + 1 for depth in _output_depths(circuit))


def test_preserves_input_and_output_order():
    function = TruthTable(
        [
            [False, True, False, True, False, True, False, True],
            [False, False, True, True, False, False, True, True],
            [False, False, False, False, True, True, True, True],
        ]
    )
    circuit = generate_circuit_pm1971(function)

    errors = []
    for assignment in itertools.product((False, True), repeat=3):
        actual = circuit.evaluate(assignment)
        expected = function.evaluate(assignment)
        if actual != expected:
            errors.append((assignment, actual, expected))

    assert not errors


@pytest.mark.parametrize("value", [False, True])
def test_constant_without_inputs(value: bool):
    circuit = generate_circuit_pm1971(TruthTable([[value]]))

    assert circuit.evaluate([]) == [value]


def test_reuses_constant_gates():
    circuit = generate_circuit_pm1971(
        TruthTable(
            [
                [False] * 4,
                [False] * 4,
                [True] * 4,
                [True] * 4,
            ]
        )
    )

    assert circuit.outputs[0] == circuit.outputs[1]
    assert circuit.outputs[2] == circuit.outputs[3]


def test_uses_documented_gate_basis():
    function = TruthTable([[False, True, True, False]])
    circuit = generate_circuit_pm1971(function)
    allowed_gate_types = {
        gate.INPUT,
        gate.NOT,
        gate.AND,
        gate.OR,
    }

    assert all(
        circuit_gate.gate_type in allowed_gate_types
        for circuit_gate in circuit.gates.values()
    )
