import collections

import pytest

from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.gate import (
    AND,
    Gate,
    GEQ,
    GT,
    INPUT,
    LEQ,
    LIFF,
    LT,
    NAND,
    NOR,
    NOT,
    NXOR,
    OR,
    XOR,
)
from cirbo.minimization.exception import UnsupportedOperationError
from cirbo.minimization.subcircuit import (
    _generate_inputs_tt,
    _get_internal_gates,
    _get_subcircuits,
    minimize_subcircuits,
)
from cirbo.synthesis.circuit_search import Basis


def test_generate_inputs_tt():
    assert _generate_inputs_tt(1) == [2]
    assert _generate_inputs_tt(2) == [10, 12]
    assert _generate_inputs_tt(3) == [170, 204, 240]
    assert _generate_inputs_tt(4) == [43690, 52428, 61680, 65280]


def test_get_subcircuits():
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', NOT, ('A',)))
    instance.add_gate(Gate('E', AND, ('B', 'D')))
    instance.add_gate(Gate('F', OR, ('A', 'C')))
    instance.add_gate(Gate('G', XOR, ('E', 'F')))
    instance.mark_as_output('G')

    cuts = [
        ('A',),
        ('B',),
        ('C',),
        ('D',),
        ('E',),
        ('F',),
        ('G',),
        ('B', 'D'),
        ('A', 'B'),
        ('A', 'C'),
        ('E', 'F'),
        ('A', 'C', 'E'),
        ('A', 'B', 'F'),
        ('A', 'B', 'C'),
        ('B', 'D', 'F'),
    ]
    nodes_for_cuts = [
        {'D', 'A'},
        {'B'},
        {'C'},
        {'D'},
        {'E'},
        {'F'},
        {'G'},
        {'E'},
        {'E'},
        {'F'},
        {'G'},
        {'G'},
        {'G'},
        {'G'},
        {'G'},
    ]
    cut_nodes = collections.defaultdict(set)
    for cut, nodes in zip(cuts, nodes_for_cuts):
        cut_nodes[cut] = nodes

    subcircuits_data = []
    for subcircuit in _get_subcircuits(instance, cuts, cut_nodes, 10, 5):
        subcircuits_data.append(
            (
                sorted(subcircuit.inputs),
                sorted(subcircuit.gates),
                sorted(subcircuit.outputs),
            )
        )

    assert len(subcircuits_data) == 4
    assert subcircuits_data[0] == (
        ['A', 'B'],
        ['A', 'B', 'D', 'E'],
        ['E'],
    )
    assert subcircuits_data[1] == (
        ['A', 'C'],
        ['A', 'C', 'D', 'F'],
        ['D', 'F'],
    )
    assert subcircuits_data[2] == (
        ['E', 'F'],
        ['E', 'F', 'G'],
        ['G'],
    )
    assert subcircuits_data[3] == (
        ['A', 'B', 'C'],
        ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
        ['G'],
    )


def test_get_internal_gates():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', NOT, ('A',)))
    instance.add_gate(Gate('F', AND, ('E', 'B')))
    instance.add_gate(Gate('G', OR, ('B', 'C')))
    instance.add_gate(Gate('H', XOR, ('F', 'G')))
    instance.add_gate(Gate('I', AND, ('D', 'A')))
    instance.add_gate(Gate('J', OR, ('I', 'E')))

    assert sorted(_get_internal_gates(instance, inputs=['A'], outputs=['E'])) == []
    assert sorted(
        _get_internal_gates(instance, inputs=['A', 'B', 'C', 'D'], outputs=['H'])
    ) == ['E', 'F', 'G']
    assert sorted(_get_internal_gates(instance, inputs=['A', 'B'], outputs=['F'])) == [
        'E'
    ]
    assert sorted(
        _get_internal_gates(instance, inputs=['A', 'B', 'C'], outputs=['H'])
    ) == ['E', 'F', 'G']
    assert sorted(
        _get_internal_gates(instance, inputs=['B', 'E', 'C'], outputs=['H'])
    ) == ['F', 'G']
    assert sorted(
        _get_internal_gates(instance, inputs=['B', 'E', 'C'], outputs=['H'])
    ) == ['F', 'G']
    assert sorted(
        _get_internal_gates(instance, inputs=['B', 'E', 'C'], outputs=['H'])
    ) == ['F', 'G']
    assert sorted(
        _get_internal_gates(instance, inputs=['A', 'B', 'C', 'D'], outputs=['H', 'J'])
    ) == ['E', 'F', 'G', 'I']
    assert sorted(_get_internal_gates(instance, inputs=[], outputs=['J'])) == [
        'A',
        'D',
        'E',
        'I',
    ]  # strange but valid query


def test_minimize_subcircuits():
    # Simple case with intersecting AND's
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('s3', AND, ('A', 'B')))
    instance.add_gate(Gate('E', AND, ('B', 'C')))
    instance.add_gate(Gate('F', AND, ('s3', 'E')))
    instance.mark_as_output('F')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.AIG, enable_validation=True
    )
    assert minimized_circuit.size == 5
    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 5

    instance.mark_as_output('s3')
    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.AIG, enable_validation=True
    )
    assert minimized_circuit.size == 5

    instance.mark_as_output('E')
    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 6


def test_minimize_subcircuits2():
    # Simple case with 2 separate simplifiable parts
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('E', INPUT))
    instance.add_gate(Gate('F', INPUT))
    instance.add_gate(Gate('AB', AND, ('A', 'B')))
    instance.add_gate(Gate('BC', AND, ('B', 'C')))
    instance.add_gate(Gate('DE', AND, ('D', 'E')))
    instance.add_gate(Gate('EF', AND, ('E', 'F')))
    instance.add_gate(Gate('X', AND, ('AB', 'BC')))
    instance.add_gate(Gate('Y', AND, ('DE', 'EF')))
    instance.add_gate(Gate('Z', XOR, ('X', 'Y')))
    instance.mark_as_output('Z')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.AIG, enable_validation=True
    )
    assert minimized_circuit.size == 11
    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 11

    instance.add_gate(Gate('G', NOT, ('Z',)))
    instance.mark_as_output('G')
    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 12


def test_minimize_subcircuits3():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', INPUT))
    instance.add_gate(Gate('AB', NAND, ('A', 'B')))
    instance.add_gate(Gate('BC', GEQ, ('B', 'C')))
    instance.add_gate(Gate('AD', GT, ('A', 'D')))
    instance.add_gate(Gate('CD', LT, ('C', 'D')))
    instance.add_gate(Gate('X', NOR, ('AB', 'CD')))
    instance.add_gate(Gate('Y', NXOR, ('BC', 'AD')))
    instance.add_gate(Gate('Z', GEQ, ('X', 'Y')))
    instance.mark_as_output('Z')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )

    assert minimized_circuit.size == 10


def test_minimize_subcircuits4():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('AB', OR, ('A', 'B')))
    instance.add_gate(Gate('C', OR, ('AB', 'A')))
    instance.add_gate(Gate('D', NOT, ('C',)))
    instance.mark_as_output('C')
    instance.mark_as_output('D')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )

    assert minimized_circuit.size == 4


def test_minimize_subcircuits5():

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('AB', OR, ('A', 'B')))
    instance.add_gate(Gate('C', AND, ('AB', 'A')))
    instance.mark_as_output('C')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )

    assert minimized_circuit.size == 3


def test_minimize_subcircuits6():
    # sum5 XAIG (size: 17 -> 16)
    instance = Circuit()

    instance.add_gate(Gate('x0', INPUT))
    instance.add_gate(Gate('x1', INPUT))
    instance.add_gate(Gate('x2', INPUT))
    instance.add_gate(Gate('x3', INPUT))
    instance.add_gate(Gate('x4', INPUT))
    instance.add_gate(Gate('z0', XOR, ('x0', 'x1')))
    instance.add_gate(Gate('z1', XOR, ('x1', 'x2')))
    instance.add_gate(Gate('z6', XOR, ('x3', 'x4')))
    instance.add_gate(Gate('z3', XOR, ('z0', 'x2')))
    instance.add_gate(Gate('z2', OR, ('z0', 'z1')))
    instance.add_gate(Gate('z5', XOR, ('z3', 'x3')))
    instance.add_gate(Gate('z4', XOR, ('z2', 'z3')))
    instance.add_gate(Gate('z7', OR, ('z5', 'z6')))
    instance.add_gate(Gate('z8', XOR, ('z5', 'x4')))
    instance.add_gate(Gate('z9', XOR, ('z7', 'z8')))
    instance.add_gate(Gate('z10', XOR, ('z4', 'z9')))
    instance.add_gate(Gate('z11', AND, ('z4', 'z9')))
    instance.mark_as_output('z8')
    instance.mark_as_output('z10')
    instance.mark_as_output('z11')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 16


def test_minimize_subcircuits7():
    # sum7 XAIG (size: 27 -> 26)
    instance = Circuit()

    instance.add_gate(Gate('x0', INPUT))
    instance.add_gate(Gate('x1', INPUT))
    instance.add_gate(Gate('x2', INPUT))
    instance.add_gate(Gate('x3', INPUT))
    instance.add_gate(Gate('x4', INPUT))
    instance.add_gate(Gate('x5', INPUT))
    instance.add_gate(Gate('x6', INPUT))
    instance.add_gate(Gate('z0', XOR, ('x0', 'x1')))
    instance.add_gate(Gate('z1', XOR, ('x1', 'x2')))
    instance.add_gate(Gate('z6', XOR, ('x3', 'x4')))
    instance.add_gate(Gate('z11', XOR, ('x5', 'x6')))
    instance.add_gate(Gate('z3', XOR, ('z0', 'x2')))
    instance.add_gate(Gate('z2', OR, ('z0', 'z1')))
    instance.add_gate(Gate('z5', XOR, ('z3', 'x3')))
    instance.add_gate(Gate('z4', XOR, ('z2', 'z3')))
    instance.add_gate(Gate('z7', OR, ('z5', 'z6')))
    instance.add_gate(Gate('z8', XOR, ('z5', 'x4')))
    instance.add_gate(Gate('z9', XOR, ('z7', 'z8')))
    instance.add_gate(Gate('z10', XOR, ('z8', 'x5')))
    instance.add_gate(Gate('z15', XOR, ('z4', 'z9')))
    instance.add_gate(Gate('z12', OR, ('z10', 'z11')))
    instance.add_gate(Gate('z13', XOR, ('z10', 'x6')))
    instance.add_gate(Gate('z14', XOR, ('z12', 'z13')))
    instance.add_gate(Gate('z16', XOR, ('z9', 'z14')))
    instance.add_gate(Gate('z18', XOR, ('z15', 'z14')))
    instance.add_gate(Gate('z17', OR, ('z15', 'z16')))
    instance.add_gate(Gate('z19', XOR, ('z17', 'z18')))
    instance.mark_as_output('z13')
    instance.mark_as_output('z18')
    instance.mark_as_output('z19')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 26


def test_exception():
    # Test exception for unsupported operations
    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', XOR, ('A', 'B')))
    instance.add_gate(Gate('E', OR, ('B', 'C')))
    instance.add_gate(Gate('F', LIFF, ('D', 'E')))
    instance.mark_as_output('F')

    with pytest.raises(UnsupportedOperationError):
        minimized_circuit = minimize_subcircuits(
            instance, basis=Basis.XAIG, enable_validation=True
        )

    instance.remove_gate('F')
    instance.add_gate(Gate('F', LEQ, ('D', 'E')))
    instance.mark_as_output('F')

    minimized_circuit = minimize_subcircuits(
        instance, basis=Basis.XAIG, enable_validation=True
    )
    assert minimized_circuit.size == 5
