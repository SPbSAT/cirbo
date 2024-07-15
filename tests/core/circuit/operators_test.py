import pytest

from boolean_circuit_tool.core.circuit.operators import (
    always_false_,
    always_true_,
    and_,
    GateState,
    geq_,
    gt_,
    iff_,
    leq_,
    liff_,
    lnot_,
    lt_,
    nand_,
    nor_,
    not_,
    nxor_,
    or_,
    riff_,
    rnot_,
    Undefined,
    xor_,
)


@pytest.mark.parametrize(
    'arg, result',
    [
        (True, False),
        (False, True),
        (Undefined, Undefined),
    ],
)
def test_not(arg: GateState, result: GateState):
    assert not_(arg) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, False),
        (False, True, False),
        (False, Undefined, False),
        (True, False, False),
        (True, True, True),
        (True, Undefined, Undefined),
        (Undefined, False, False),
        (Undefined, True, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_and_2(arg1: GateState, arg2: GateState, result: GateState):
    assert and_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, False),
        (False, False, True, False),
        (False, False, Undefined, False),
        (False, True, False, False),
        (False, True, True, False),
        (False, True, Undefined, False),
        (False, Undefined, False, False),
        (False, Undefined, True, False),
        (
            False,
            Undefined,
            Undefined,
            False,
        ),
        (True, False, False, False),
        (True, False, True, False),
        (True, False, Undefined, False),
        (True, True, False, False),
        (True, True, True, True),
        (True, True, Undefined, Undefined),
        (True, Undefined, False, False),
        (True, Undefined, True, Undefined),
        (
            True,
            Undefined,
            Undefined,
            Undefined,
        ),
        (Undefined, False, False, False),
        (Undefined, False, True, False),
        (
            Undefined,
            False,
            Undefined,
            False,
        ),
        (Undefined, True, False, False),
        (Undefined, True, True, Undefined),
        (
            Undefined,
            True,
            Undefined,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            False,
            False,
        ),
        (
            Undefined,
            Undefined,
            True,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_and_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert and_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, True),
        (False, True, True),
        (False, Undefined, True),
        (True, False, True),
        (True, True, False),
        (True, Undefined, Undefined),
        (Undefined, False, True),
        (Undefined, True, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_nand_2(arg1: GateState, arg2: GateState, result: GateState):
    assert nand_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, True),
        (False, False, True, True),
        (False, False, Undefined, True),
        (False, True, False, True),
        (False, True, True, True),
        (False, True, Undefined, True),
        (False, Undefined, False, True),
        (False, Undefined, True, True),
        (False, Undefined, Undefined, True),
        (True, False, False, True),
        (True, False, True, True),
        (True, False, Undefined, True),
        (True, True, False, True),
        (True, True, True, False),
        (True, True, Undefined, Undefined),
        (True, Undefined, False, True),
        (True, Undefined, True, Undefined),
        (
            True,
            Undefined,
            Undefined,
            Undefined,
        ),
        (Undefined, False, False, True),
        (Undefined, False, True, True),
        (Undefined, False, Undefined, True),
        (Undefined, True, False, True),
        (Undefined, True, True, Undefined),
        (
            Undefined,
            True,
            Undefined,
            Undefined,
        ),
        (Undefined, Undefined, False, True),
        (
            Undefined,
            Undefined,
            True,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_nand_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert nand_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, False),
        (False, True, True),
        (False, Undefined, Undefined),
        (True, False, True),
        (True, True, True),
        (True, Undefined, True),
        (Undefined, False, Undefined),
        (Undefined, True, True),
        (Undefined, Undefined, Undefined),
    ],
)
def test_or_2(arg1: GateState, arg2: GateState, result: GateState):
    assert or_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, False),
        (False, False, True, True),
        (
            False,
            False,
            Undefined,
            Undefined,
        ),
        (False, True, False, True),
        (False, True, True, True),
        (False, True, Undefined, True),
        (
            False,
            Undefined,
            False,
            Undefined,
        ),
        (False, Undefined, True, True),
        (
            False,
            Undefined,
            Undefined,
            Undefined,
        ),
        (True, False, False, True),
        (True, False, True, True),
        (True, False, Undefined, True),
        (True, True, False, True),
        (True, True, True, True),
        (True, True, Undefined, True),
        (True, Undefined, False, True),
        (True, Undefined, True, True),
        (True, Undefined, Undefined, True),
        (
            Undefined,
            False,
            False,
            Undefined,
        ),
        (Undefined, False, True, True),
        (
            Undefined,
            False,
            Undefined,
            Undefined,
        ),
        (Undefined, True, False, True),
        (Undefined, True, True, True),
        (Undefined, True, Undefined, True),
        (
            Undefined,
            Undefined,
            False,
            Undefined,
        ),
        (Undefined, Undefined, True, True),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_or_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert or_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, True),
        (False, True, False),
        (False, Undefined, Undefined),
        (True, False, False),
        (True, True, False),
        (True, Undefined, False),
        (Undefined, False, Undefined),
        (Undefined, True, False),
        (Undefined, Undefined, Undefined),
    ],
)
def test_nor_2(arg1: GateState, arg2: GateState, result: GateState):
    assert nor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, True),
        (False, False, True, False),
        (
            False,
            False,
            Undefined,
            Undefined,
        ),
        (False, True, False, False),
        (False, True, True, False),
        (False, True, Undefined, False),
        (
            False,
            Undefined,
            False,
            Undefined,
        ),
        (False, Undefined, True, False),
        (
            False,
            Undefined,
            Undefined,
            Undefined,
        ),
        (True, False, False, False),
        (True, False, True, False),
        (True, False, Undefined, False),
        (True, True, False, False),
        (True, True, True, False),
        (True, True, Undefined, False),
        (True, Undefined, False, False),
        (True, Undefined, True, False),
        (True, Undefined, Undefined, False),
        (
            Undefined,
            False,
            False,
            Undefined,
        ),
        (Undefined, False, True, False),
        (
            Undefined,
            False,
            Undefined,
            Undefined,
        ),
        (Undefined, True, False, False),
        (Undefined, True, True, False),
        (Undefined, True, Undefined, False),
        (
            Undefined,
            Undefined,
            False,
            Undefined,
        ),
        (Undefined, Undefined, True, False),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_nor_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert nor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, False),
        (False, True, True),
        (False, Undefined, Undefined),
        (True, False, True),
        (True, True, False),
        (True, Undefined, Undefined),
        (Undefined, False, Undefined),
        (Undefined, True, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_xor_2(arg1: GateState, arg2: GateState, result: GateState):
    assert xor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, False),
        (False, False, True, True),
        (
            False,
            False,
            Undefined,
            Undefined,
        ),
        (False, True, False, True),
        (False, True, True, False),
        (False, True, Undefined, Undefined),
        (
            False,
            Undefined,
            False,
            Undefined,
        ),
        (False, Undefined, True, Undefined),
        (
            False,
            Undefined,
            Undefined,
            Undefined,
        ),
        (True, False, False, True),
        (True, False, True, False),
        (True, False, Undefined, Undefined),
        (True, True, False, False),
        (True, True, True, True),
        (True, True, Undefined, Undefined),
        (True, Undefined, False, Undefined),
        (True, Undefined, True, Undefined),
        (
            True,
            Undefined,
            Undefined,
            Undefined,
        ),
        (
            Undefined,
            False,
            False,
            Undefined,
        ),
        (Undefined, False, True, Undefined),
        (
            Undefined,
            False,
            Undefined,
            Undefined,
        ),
        (Undefined, True, False, Undefined),
        (Undefined, True, True, Undefined),
        (
            Undefined,
            True,
            Undefined,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            False,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            True,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_xor_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert xor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (False, False, True),
        (False, True, False),
        (False, Undefined, Undefined),
        (True, False, False),
        (True, True, True),
        (True, Undefined, Undefined),
        (Undefined, False, Undefined),
        (Undefined, True, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_nxor_2(arg1: GateState, arg2: GateState, result: GateState):
    assert nxor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (False, False, False, True),
        (False, False, True, False),
        (
            False,
            False,
            Undefined,
            Undefined,
        ),
        (False, True, False, False),
        (False, True, True, True),
        (False, True, Undefined, Undefined),
        (
            False,
            Undefined,
            False,
            Undefined,
        ),
        (False, Undefined, True, Undefined),
        (
            False,
            Undefined,
            Undefined,
            Undefined,
        ),
        (True, False, False, False),
        (True, False, True, True),
        (True, False, Undefined, Undefined),
        (True, True, False, True),
        (True, True, True, False),
        (True, True, Undefined, Undefined),
        (True, Undefined, False, Undefined),
        (True, Undefined, True, Undefined),
        (
            True,
            Undefined,
            Undefined,
            Undefined,
        ),
        (
            Undefined,
            False,
            False,
            Undefined,
        ),
        (Undefined, False, True, Undefined),
        (
            Undefined,
            False,
            Undefined,
            Undefined,
        ),
        (Undefined, True, False, Undefined),
        (Undefined, True, True, Undefined),
        (
            Undefined,
            True,
            Undefined,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            False,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            True,
            Undefined,
        ),
        (
            Undefined,
            Undefined,
            Undefined,
            Undefined,
        ),
    ],
)
def test_nxor_3(arg1: GateState, arg2: GateState, arg3: GateState, result: GateState):
    assert nxor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg, result',
    [
        (True, True),
        (False, False),
        (Undefined, Undefined),
    ],
)
def test_iff(arg: GateState, result: GateState):
    assert iff_(arg) == result


def test_always_true0():
    assert always_true_() == True


@pytest.mark.parametrize(
    'arg',
    [
        True,
        False,
        Undefined,
    ],
)
def test_always_true1(arg: GateState):
    assert always_true_(arg) == True


@pytest.mark.parametrize(
    'arg1, arg2',
    [
        (True, True),
        (True, False),
        (True, Undefined),
        (False, True),
        (False, False),
        (False, Undefined),
        (Undefined, True),
        (Undefined, False),
        (Undefined, Undefined),
    ],
)
def test_always_true2(arg1: GateState, arg2: GateState):
    assert always_true_(arg1, arg2) == True


def test_always_false0():
    assert always_false_() == False


@pytest.mark.parametrize(
    'arg',
    [
        True,
        False,
        Undefined,
    ],
)
def test_always_false1(arg: GateState):
    assert always_false_(arg) == False


@pytest.mark.parametrize(
    'arg1, arg2',
    [
        (True, True),
        (True, False),
        (True, Undefined),
        (False, True),
        (False, False),
        (False, Undefined),
        (Undefined, True),
        (Undefined, False),
        (Undefined, Undefined),
    ],
)
def test_always_false2(arg1: GateState, arg2: GateState):
    assert always_false_(arg1, arg2) == False


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (True, False, True),
        (True, Undefined, Undefined),
        (False, True, False),
        (False, False, True),
        (False, Undefined, Undefined),
        (Undefined, True, False),
        (Undefined, False, True),
        (Undefined, Undefined, Undefined),
    ],
)
def test_rnot(arg1: GateState, arg2: GateState, result: GateState):
    assert rnot_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (True, False, False),
        (True, Undefined, False),
        (False, True, True),
        (False, False, True),
        (False, Undefined, True),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_lnot(arg1: GateState, arg2: GateState, result: GateState):
    assert lnot_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2',
    [
        (True, True),
        (True, False),
        (True, Undefined),
        (False, True),
        (False, False),
        (False, Undefined),
        (Undefined, True),
        (Undefined, False),
        (Undefined, Undefined),
    ],
)
def test_riff(arg1: GateState, arg2: GateState):
    assert riff_(arg1, arg2) == arg2


@pytest.mark.parametrize(
    'arg1, arg2',
    [
        (True, True),
        (True, False),
        (True, Undefined),
        (False, True),
        (False, False),
        (False, Undefined),
        (Undefined, True),
        (Undefined, False),
        (Undefined, Undefined),
    ],
)
def test_liff(arg1: GateState, arg2: GateState):
    assert liff_(arg1, arg2) == arg1


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (True, False, True),
        (True, Undefined, Undefined),
        (False, True, False),
        (False, False, False),
        (False, Undefined, False),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_gt_(arg1: GateState, arg2: GateState, result: GateState):
    assert gt_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (True, False, False),
        (True, Undefined, False),
        (False, True, True),
        (False, False, False),
        (False, Undefined, Undefined),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_lt_(arg1: GateState, arg2: GateState, result: GateState):
    assert lt_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (True, False, True),
        (True, Undefined, True),
        (False, True, False),
        (False, False, True),
        (False, Undefined, Undefined),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_geq_(arg1: GateState, arg2: GateState, result: GateState):
    assert geq_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (True, False, False),
        (True, Undefined, Undefined),
        (False, True, True),
        (False, False, True),
        (False, Undefined, True),
        (Undefined, True, Undefined),
        (Undefined, False, Undefined),
        (Undefined, Undefined, Undefined),
    ],
)
def test_leq_(arg1: GateState, arg2: GateState, result: GateState):
    assert leq_(arg1, arg2) == result
