import abc
import dataclasses
import pathlib

from cirbo.core import Circuit


@dataclasses.dataclass
class InstanceDescriptor:
    path: pathlib.Path
    depth: int
    size: int


class InstanceAccessor(metaclass=abc.ABCMeta):
    def __init__(self, instance_descriptor: InstanceDescriptor):
        super().__init__(self)
        self.instance_info = instance_descriptor

    @abc.abstractmethod
    def load(self) -> Circuit:
        raise NotImplementedError()


class InstanceFront: ...


class InstanceParetoFront: ...
