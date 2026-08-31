import abc
import dataclasses
import pathlib
import typing as tp

from cirbo.core import Circuit


@dataclasses.dataclass
class InstanceDescriptor:
    """
    Describes an instance of a circuit to be minimized.

    """

    instance: tp.Union[pathlib.Path, Circuit]
    depth: int
    size: int

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> "InstanceDescriptor":
        return InstanceDescriptor(
            instance=circuit,
            depth=circuit.get_depth(),
            size=circuit.size,
        )

    def dominates(self, other: "InstanceDescriptor") -> bool:
        return self.size >= other.size and self.depth >= other.depth and self != other


class InstanceAccessor(metaclass=abc.ABCMeta):
    def __init__(self, instance_descriptor: InstanceDescriptor):
        super().__init__(self)
        self.instance_info = instance_descriptor

    @abc.abstractmethod
    def load(self) -> Circuit:
        raise NotImplementedError()


class InstanceFront(metaclass=abc.ABCMeta):
    def __init__(self):
        self.instances: tp.List[InstanceDescriptor] = []

    @abc.abstractmethod
    def rebuild(self, new_instance: InstanceDescriptor) -> "InstanceFront":
        raise NotImplementedError


class InstanceParetoFront(InstanceFront): ...
