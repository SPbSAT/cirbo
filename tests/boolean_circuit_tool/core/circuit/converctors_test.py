import copy

import pytest

from boolean_circuit_tool.core.circuit import gate
from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.exceptions import GateDoesntExistError


@pytest.mark.parametrize(
    'type',
    [
        gate.AND,
        gate.GEQ,
        gate.GT,
        gate.LEQ,
        gate.LIFF,
        gate.LNOT,
        gate.LT,
        gate.NAND,
        gate.NOR,
        gate.NXOR,
        gate.OR,
        gate.RIFF,
        gate.RNOT,
        gate.XOR,
    ],
)
def test_simple(type: gate.GateType):
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', type, ('A', 'B')))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()


def test_always_true():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_TRUE))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()

    C0 = Circuit().add_gate(gate.Gate('A', gate.ALWAYS_TRUE))
    with pytest.raises(GateDoesntExistError):
        C0.into_bench()


def test_always_false():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.ALWAYS_FALSE))
    )

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()

    C0 = Circuit().add_gate(gate.Gate('A', gate.ALWAYS_FALSE))
    with pytest.raises(GateDoesntExistError):
        C0.into_bench()


def test_mix_ckt_gates():

    C0 = Circuit()

    C0.add_gate(gate.Gate('1', gate.INPUT))
    C0.add_gate(gate.Gate('2', gate.INPUT))
    C0.add_gate(gate.Gate('3', gate.NOT, ('1',)))
    C0.add_gate(gate.Gate('4', gate.AND, ('1', '2')))
    C0.add_gate(gate.Gate('5', gate.XOR, ('1', '2')))
    C0.add_gate(gate.Gate('6', gate.AND, ('2', '4')))
    C0.add_gate(gate.Gate('7', gate.ALWAYS_FALSE))
    C0.add_gate(gate.Gate('8', gate.ALWAYS_TRUE, ('1',)))
    C0.add_gate(gate.Gate('9', gate.LNOT, ('7', '3')))
    C0.add_gate(gate.Gate('10', gate.RNOT, ('4', '8')))
    C0.add_gate(gate.Gate('11', gate.LEQ, ('2', '4')))
    C0.add_gate(gate.Gate('12', gate.LT, ('2', '11')))
    C0.add_gate(gate.Gate('13', gate.GEQ, ('11', '12')))
    C0.add_gate(gate.Gate('14', gate.GT, ('13', '5')))
    C0.add_gate(gate.Gate('15', gate.IFF, ('14',)))
    C0.add_gate(gate.Gate('16', gate.LIFF, ('15', '5')))
    C0.add_gate(gate.Gate('17', gate.RIFF, ('13', '16')))

    C0.mark_as_output('17')

    C1 = copy.copy(C0)
    C1.into_bench()

    assert C0.get_truth_table() == C1.get_truth_table()


def test_block():
    C0 = (
        Circuit()
        .add_gate(gate.Gate('A', gate.INPUT))
        .add_gate(gate.Gate('B', gate.INPUT))
        .add_gate(gate.Gate('C', gate.LT, ('A', 'B')))
        .add_gate(gate.Gate('D', gate.AND, ('B', 'C')))
    )
    C0.mark_as_output('C')

    C0.make_block_from_slice('new_block', C0.inputs, ['C'])
    assert C0._blocks['new_block'].gates == ['C']

    C0.into_bench()
    assert len(C0._blocks['new_block'].gates) == 2
