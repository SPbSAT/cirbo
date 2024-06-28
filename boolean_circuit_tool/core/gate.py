"""Implementation gate's class."""

import enum
import typing as tp

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
    MUX = "MUX"


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

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label}, {self._gate_type}, {self._operands})"

    def __str__(self):
        return f"{self._label} = {self.gate_type.value}({', '.join(self._operands)})"
