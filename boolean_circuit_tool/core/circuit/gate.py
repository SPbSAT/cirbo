"""Module defines Gate and related objects."""

import typing as tp
from dataclasses import dataclass

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
    'INPUT',
    'NOT',
    'OR',
    'NOR',
    'AND',
    'NAND',
    'XOR',
    'NXOR',
    'IFF',
    'BUFF',
]

GateLabel = str


@dataclass
class GateType:
    """Class possible types of operator gate."""

    _name: str
    _operator: tp.Callable
    _is_symmetric: bool

    @property
    def operator(self) -> tp.Callable:
        return self._operator

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_symmetric(self) -> bool:
        return self._is_symmetric

    def __eq__(self, rhs):
        return isinstance(rhs, GateType) and self._name == rhs._name


INPUT = GateType("INPUT", lambda: None, True)
NOT = GateType("NOT", not_, True)
OR = GateType("OR", or_, True)
NOR = GateType("NOR", nor_, True)
AND = GateType("AND", and_, True)
NAND = GateType("NAND", nand_, True)
XOR = GateType("XOR", xor_, False)
NXOR = GateType("NXOR", nxor_, False)
IFF = GateType("IFF", iff_, True)
BUFF = GateType("BUFF", iff_, True)


class Gate:
    """Structure to carry one Gate of a Circuit."""

    def __init__(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
    ):
        self._label: GateLabel = label
        self._gate_type: GateType = gate_type
        self._operands: tuple[GateLabel, ...] = operands
        self._users: list[GateLabel] = list()

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
        for operand in self._operands:
            yield operand

    @property
    def users(self) -> tp.Iterable[GateLabel]:
        """Return gate's users in iterable object."""
        for user in self._users:
            yield user

    @property
    def operator(self) -> tp.Callable:
        return self._gate_type.operator

    def _add_users(self, *users: GateLabel) -> None:
        for user in users:
            if user not in self._users:
                self._users.append(user)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._label}, {self._gate_type}, {self._operands})"

    def __str__(self):
        if self.gate_type == INPUT:
            return f"INPUT({self._label})"
        else:
            return (
                f"{self._label} = {self.gate_type.value}({', '.join(self._operands)})"
            )
