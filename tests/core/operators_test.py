from boolean_circuit_tool.core.gate import GateAssign
from boolean_circuit_tool.core.operators import (
    and_,
    iff_,
    mux_,
    nand_,
    nor_,
    not_,
    nxor_,
    or_,
    xor_,
)


def test_not():
    assert not_(GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert not_(GateAssign.FALSE.value) == GateAssign.TRUE.value


def test_and():
    assert and_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert and_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert and_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value
    assert (
        and_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value
    )

    assert (
        and_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        and_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        and_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )


def test_nand():
    assert nand_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert nand_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert nand_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value
    assert (
        nand_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value
    )

    assert (
        nand_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nand_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nand_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )


def test_or():
    assert or_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert or_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert or_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value
    assert or_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value

    assert (
        or_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        or_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )


def test_nor_():
    assert nor_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert nor_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert nor_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value
    assert nor_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value

    assert (
        nor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )


def test_xor():
    assert xor_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    assert xor_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert xor_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value
    assert (
        xor_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value
    )

    assert (
        xor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        xor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        xor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        xor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        xor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        xor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        xor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        xor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )


def test_nxor_():
    assert nxor_(GateAssign.TRUE.value, GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.TRUE.value) == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.TRUE.value, GateAssign.FALSE.value) == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.FALSE.value) == GateAssign.TRUE.value
    )

    assert (
        nxor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nxor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        nxor_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )


def test_iff():
    assert iff_(GateAssign.TRUE.value) == GateAssign.TRUE.value
    assert iff_(GateAssign.FALSE.value) == GateAssign.FALSE.value


def test_mux_():
    assert (
        mux_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        mux_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        mux_(GateAssign.TRUE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
    assert (
        mux_(GateAssign.TRUE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )

    assert (
        mux_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.TRUE.value)
        == GateAssign.TRUE.value
    )
    assert (
        mux_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.TRUE.value)
        == GateAssign.FALSE.value
    )
    assert (
        mux_(GateAssign.FALSE.value, GateAssign.TRUE.value, GateAssign.FALSE.value)
        == GateAssign.TRUE.value
    )
    assert (
        mux_(GateAssign.FALSE.value, GateAssign.FALSE.value, GateAssign.FALSE.value)
        == GateAssign.FALSE.value
    )
