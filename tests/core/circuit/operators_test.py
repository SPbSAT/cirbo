import pytest

from boolean_circuit_tool.core.circuit.operators import (
    and_,
    GateAssign,
    iff_,
    nand_,
    nor_,
    not_,
    nxor_,
    or_,
    xor_,
)


@pytest.mark.parametrize(
    'arg, result',
    [
        (GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_not(arg: GateAssign, result: GateAssign):
    assert not_(arg) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_and_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert and_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
        ),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
        ),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.FALSE,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_and_3(
    arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign
):
    assert and_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_nand_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert nand_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_nand_3(
    arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign
):
    assert nand_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_or_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert or_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.TRUE),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_or_3(arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign):
    assert or_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_nor_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert nor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.FALSE),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_nor_3(
    arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign
):
    assert nor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_xor_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert xor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_xor_3(
    arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign
):
    assert xor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_nxor_2(arg1: GateAssign, arg2: GateAssign, result: GateAssign):
    assert nxor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE),
        (
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE, GateAssign.TRUE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.TRUE, GateAssign.FALSE),
        (GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.TRUE, GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.FALSE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.FALSE, GateAssign.UNDEFINED),
        (GateAssign.UNDEFINED, GateAssign.TRUE, GateAssign.TRUE, GateAssign.UNDEFINED),
        (
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.FALSE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.TRUE,
            GateAssign.UNDEFINED,
        ),
        (
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
            GateAssign.UNDEFINED,
        ),
    ],
)
def test_nxor_3(
    arg1: GateAssign, arg2: GateAssign, arg3: GateAssign, result: GateAssign
):
    assert nxor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg, result',
    [
        (GateAssign.TRUE, GateAssign.TRUE),
        (GateAssign.FALSE, GateAssign.FALSE),
        (GateAssign.UNDEFINED, GateAssign.UNDEFINED),
    ],
)
def test_iff(arg: GateAssign, result: GateAssign):
    assert iff_(arg) == result
