"""Module defines Gate and related objects."""

import dataclasses
import typing as tp

from boolean_circuit_tool.core.circuit.exceptions import GateTypeNoOperatorError
from boolean_circuit_tool.core.circuit.operators import (
    always_false_,
    always_true_,
    and_,
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
    xor_,
)


__all__ = [
    'Gate',
    'GateType',
    'Label',
    'INPUT',
    'ALWAYS_FALSE',
    'ALWAYS_TRUE',
    'AND',
    'GEQ',
    'GT',
    'IFF',
    'LEQ',
    'LIFF',
    'LNOT',
    'LT',
    'NAND',
    'NOR',
    'NOT',
    'NXOR',
    'OR',
    'RIFF',
    'RNOT',
    'XOR',
]

Label = str


@dataclasses.dataclass(eq=False, unsafe_hash=False, frozen=True)
class GateType:
    """Class possible types of operator gate."""

    _name: str
    _operator: tp.Optional[tp.Callable]
    _is_symmetric: bool

    @property
    def operator(self) -> tp.Callable:
        """Returns callable that can evaluate gate of this type."""
        if self._operator is None:
            raise GateTypeNoOperatorError()
        return self._operator

    @property
    def name(self) -> str:
        """Returns name of this type."""
        return self._name

    @property
    def is_symmetric(self) -> bool:
        """Returns True iff gate of this type does not depend on order of operands."""
        return self._is_symmetric

    def __eq__(self, rhs):
        if not isinstance(rhs, GateType):
            return NotImplemented

        return (
            True
            and self._name == rhs._name
            and self._operator == rhs._operator
            and self._is_symmetric == rhs._is_symmetric
        )

    def __hash__(self) -> int:
        return hash(self.name)


INPUT = GateType("INPUT", None, True)
ALWAYS_TRUE = GateType("ALWAYS_TRUE", always_true_, True)
ALWAYS_FALSE = GateType("ALWAYS_FALSE", always_false_, True)
AND = GateType("AND", and_, True)
GEQ = GateType("GEQ", geq_, False)
GT = GateType("GT", gt_, False)
IFF = GateType("IFF", iff_, True)
LEQ = GateType("LEQ", leq_, False)
LIFF = GateType("LIFF", liff_, False)
LNOT = GateType("LNOT", lnot_, False)
LT = GateType("LT", lt_, False)
NAND = GateType("NAND", nand_, True)
NOR = GateType("NOR", nor_, True)
NOT = GateType("NOT", not_, True)
NXOR = GateType("NXOR", nxor_, True)
OR = GateType("OR", or_, True)
RIFF = GateType("RIFF", riff_, False)
RNOT = GateType("RNOT", rnot_, False)
XOR = GateType("XOR", xor_, True)


class Gate:
    """Structure to carry one Gate of a Circuit."""

    def __init__(
        self,
        label: Label,
        gate_type: GateType,
        operands: tuple[Label, ...] = (),
    ):
        self._label: Label = label
        self._gate_type: GateType = gate_type
        self._operands: tuple[Label, ...] = operands

    @property
    def label(self) -> Label:
        """Return gate's name."""
        return self._label

    @property
    def gate_type(self) -> GateType:
        """Return gate's type."""
        return self._gate_type

    @property
    def operands(self) -> tuple[Label, ...]:
        """Return gate's operands in iterable object."""
        return self._operands

    @property
    def operator(self) -> tp.Callable:
        """Callable operator that evaluates this gate."""
        return self._gate_type.operator

    def format_gate(self):
        if self.gate_type == INPUT:
            return f"INPUT({self._label})"
        return f"{self._label} = {self.gate_type.name}({', '.join(self._operands)})"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Gate):
            return NotImplemented
        return (
            True
            and self.label == value.label
            and self.gate_type == value.gate_type
            and self.operands == value.operands
        )

    def __hash__(self) -> int:
        return hash((self.label, self.gate_type, self.operands))

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label}, {self._gate_type}, {self._operands})"

    def __str__(self):
        return (
            f"{self.__class__.__name__}"
            + f"({self._label}, {self._gate_type.name}, {self._operands})"
        )
