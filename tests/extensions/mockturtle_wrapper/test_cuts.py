import mockturtle_wrapper as mw
from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.gate import AND, Gate, INPUT, NOT, OR, XOR


def test_enumerate_cuts():
    assert callable(mw.enumerate_cuts)

    instance = Circuit()

    instance.add_gate(Gate('A', INPUT))
    instance.add_gate(Gate('B', INPUT))
    instance.add_gate(Gate('C', INPUT))
    instance.add_gate(Gate('D', NOT, ('A',)))
    instance.add_gate(Gate('E', AND, ('B', 'D')))
    instance.add_gate(Gate('F', OR, ('A', 'C')))
    instance.add_gate(Gate('G', XOR, ('E', 'F')))
    instance.mark_as_output('G')

    node_cuts = {
        'A': [['A']],
        'B': [['B']],
        'C': [['C']],
        'D': [['A'], ['D']],
        'E': [['B', 'D'], ['A', 'B'], ['E']],
        'F': [['A', 'C'], ['F']],
        'G': [
            ['E', 'F'],
            ['A', 'C', 'E'],
            ['A', 'B', 'F'],
            ['A', 'B', 'C'],
            ['B', 'D', 'F'],
            ['G'],
        ],
    }

    assert (
        mw.enumerate_cuts(
            instance.format_circuit(),
            5,
            50,
            10000,
        )
        == node_cuts
    )
