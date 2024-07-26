import typing as tp
from typing import List, Tuple

import pytest
from boolean_circuit_tool.cnf import CnfRaw, Tseytin

from boolean_circuit_tool.core.circuit import AND, Circuit, Gate, INPUT, NOT, OR, XOR


def generate_circuit1() -> tuple[Circuit, CnfRaw]:
    circuit = Circuit()
    circuit.add_gate(Gate('A', INPUT))
    circuit.add_gate(Gate('B', INPUT))

    circuit.add_gate(
        Gate(
            'C',
            AND,
            (
                'A',
                'B',
            ),
        )
    )

    circuit.mark_as_output('C')
    return circuit, [[1, -3], [2, -3], [3, -1, -2], [3]]


def generate_circuit2() -> tuple[Circuit, CnfRaw]:
    circuit = Circuit()
    circuit.add_gate(Gate('A', INPUT))
    circuit.add_gate(Gate('B', INPUT))
    circuit.add_gate(Gate('C', INPUT))

    circuit.add_gate(Gate('D', NOT, ('B',)))
    circuit.add_gate(
        Gate(
            'E',
            OR,
            (
                'A',
                'D',
            ),
        )
    )
    circuit.add_gate(
        Gate(
            'F',
            AND,
            (
                'D',
                'E',
            ),
        )
    )

    circuit.mark_as_output('F')
    return circuit, [
        [2, 4],
        [-2, -4],
        [2, 4],
        [-2, -4],
        [-1, 5],
        [-4, 5],
        [-5, 1, 4],
        [4, -6],
        [5, -6],
        [6, -4, -5],
        [6],
    ]


def generate_circuit3() -> tuple[Circuit, CnfRaw]:
    circuit = Circuit()
    circuit.add_gate(Gate('A', INPUT))
    circuit.add_gate(Gate('B', INPUT))
    circuit.add_gate(Gate('C', INPUT))

    circuit.add_gate(Gate('D', NOT, ('A',)))
    circuit.add_gate(Gate('E', NOT, ('C',)))
    circuit.add_gate(
        Gate(
            'F',
            XOR,
            (
                'D',
                'B',
            ),
        )
    )
    circuit.add_gate(
        Gate(
            'G',
            XOR,
            (
                'F',
                'E',
            ),
        )
    )

    circuit.mark_as_output('G')
    return circuit, [
        [1, 4],
        [-1, -4],
        [-4, -2, -5],
        [-4, 2, 5],
        [4, -2, 5],
        [4, 2, -5],
        [3, 6],
        [-3, -6],
        [-5, -6, -7],
        [-5, 6, 7],
        [5, -6, 7],
        [5, 6, -7],
        [7],
    ]


@pytest.mark.parametrize(
    'generate_circuit',
    [
        generate_circuit1,
        generate_circuit2,
        generate_circuit3,
    ],
)
def test_tseytin(generate_circuit: tp.Callable[[], tp.Tuple[Circuit, CnfRaw]]):
    circuit, expected_cnf = generate_circuit()
    cnf = Tseytin(circuit).to_cnf()
    print(cnf)
    assert cnf == expected_cnf
