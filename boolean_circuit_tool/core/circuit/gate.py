"""Module defines Gate and related objects."""

import enum
import typing as tp

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

__all__ = [
    'Gate',
    'GateLabel',
    'GateType',
    'GateAssign',
]

GateLabel = str


class GateType(enum.Enum):
    """Possible types of operator gate."""

    INPUT = "INPUT"
    NOT = "NOT"
    OR = "OR"
    NOR = "NOR"
    AND = "AND"
    NAND = "NAND"
    XOR = "XOR"
    NXOR = "NXOR"
    IFF = "IFF"
    BUFF = "BUFF"


class GateAssign(enum.Enum):
    UNDEFINED = -1
    FALSE = False
    TRUE = True


class Gate:
    """Structure to carry one Gate of a Circuit."""

    def __init__(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
    ):
        self._label = label
        self._gate_type = gate_type
        self._operands = operands

    @property
    def label(self) -> GateLabel:
        """Return gate's name."""
        return self._label

    @property
    def gate_type(self) -> GateType:
        """Return gate's type."""
        return self._gate_type

    @property
    def operands(self) -> tp.Iterable[GateLabel]:
        """Return gate's operands in iterable object."""
        for oper in self._operands:
            yield oper

    @property
    def operator(self):
        return {
            GateType.NOT: not_,
            GateType.AND: and_,
            GateType.NAND: nand_,
            GateType.OR: or_,
            GateType.NOR: nor_,
            GateType.XOR: xor_,
            GateType.NXOR: nxor_,
            GateType.IFF: iff_,
            GateType.BUFF: iff_,
        }[self._gate_type]

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label}, {self._gate_type}, {self._operands})"

    def __str__(self):
        if self.gate_type == GateType.INPUT:
            return f"INPUT({self._label})"
        else:
            return (
                f"{self._label} = {self.gate_type.value}({', '.join(self._operands)})"
            )
