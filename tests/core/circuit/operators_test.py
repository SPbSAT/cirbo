import pytest

from boolean_circuit_tool.core.circuit.operators import (
    and_,
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
        (True, False),
        (False, True),
    ],
)
def test_not(arg: bool, result: bool):
    assert not_(arg) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (False, True, False),
        (True, False, False),
        (False, False, False),
    ],
)
def test_and_2(arg1: bool, arg2: bool, result: bool):
    assert and_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, True),
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, False),
        (False, True, True, False),
        (False, True, False, False),
        (False, False, True, False),
        (False, False, False, False),
    ],
)
def test_and_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert and_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (False, True, True),
        (True, False, True),
        (False, False, True),
    ],
)
def test_nand_2(arg1: bool, arg2: bool, result: bool):
    assert nand_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, False),
        (True, True, False, True),
        (True, False, True, True),
        (True, False, False, True),
        (False, True, True, True),
        (False, True, False, True),
        (False, False, True, True),
        (False, False, False, True),
    ],
)
def test_nand_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert nand_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (False, True, True),
        (True, False, True),
        (False, False, False),
    ],
)
def test_or_2(arg1: bool, arg2: bool, result: bool):
    assert or_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, True),
        (True, True, False, True),
        (True, False, True, True),
        (True, False, False, True),
        (False, True, True, True),
        (False, True, False, True),
        (False, False, True, True),
        (False, False, False, False),
    ],
)
def test_or_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert or_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (False, True, False),
        (True, False, False),
        (False, False, True),
    ],
)
def test_nor_2(arg1: bool, arg2: bool, result: bool):
    assert nor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, False),
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, False),
        (False, True, True, False),
        (False, True, False, False),
        (False, False, True, False),
        (False, False, False, True),
    ],
)
def test_nor_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert nor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, False),
        (False, True, True),
        (True, False, True),
        (False, False, False),
    ],
)
def test_xor_2(arg1: bool, arg2: bool, result: bool):
    assert xor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, True),
        (True, True, False, False),
        (True, False, True, False),
        (True, False, False, True),
        (False, True, True, False),
        (False, True, False, True),
        (False, False, True, True),
        (False, False, False, False),
    ],
)
def test_xor_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert xor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg1, arg2, result',
    [
        (True, True, True),
        (False, True, False),
        (True, False, False),
        (False, False, True),
    ],
)
def test_nxor_2(arg1: bool, arg2: bool, result: bool):
    assert nxor_(arg1, arg2) == result


@pytest.mark.parametrize(
    'arg1, arg2, arg3, result',
    [
        (True, True, True, False),
        (True, True, False, True),
        (True, False, True, True),
        (True, False, False, False),
        (False, True, True, True),
        (False, True, False, False),
        (False, False, True, False),
        (False, False, False, True),
    ],
)
def test_nxor_3(arg1: bool, arg2: bool, arg3: bool, result: bool):
    assert nxor_(arg1, arg2, arg3) == result


@pytest.mark.parametrize(
    'arg, result',
    [
        (True, True),
        (False, False),
    ],
)
def test_iff(arg: bool, result: bool):
    assert iff_(arg) == result
