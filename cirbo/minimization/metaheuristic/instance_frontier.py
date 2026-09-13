import abc
import dataclasses
import os
import pathlib
import random
import shutil
import typing as tp

import typing_extensions as tp_ext

from cirbo.core import Circuit
from cirbo.core.circuit import gate
from cirbo.sat.sat import check_circuits_equivalence
from .exceptions import InvalidFrontierError

__all__ = [
    'CircuitStats',
    'InstanceDescriptor',
    'InstanceFrontier',
    'ParetoFrontier',
]


@dataclasses.dataclass(frozen=True, order=True)
class CircuitStats:
    """
    Objective values used by the built-in Pareto search.

    Depth ans Size doesn't include LNOT, RNOT, IFF, LIFF, RIFF gates.
    """

    depth: int
    size: int

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> "CircuitStats":
        """Measure gate count and the longest non-input gate path to an output."""
        return CircuitStats(
            depth=circuit.get_depth(),
            size=circuit.gates_number(),
        )

    def dominates(self, other: "CircuitStats") -> bool:
        """Return True if self dominates other."""
        return self.size <= other.size and self.depth <= other.depth and self != other

    def __str__(self) -> str:
        return f"(size={self.size}, depth={self.depth})"


@dataclasses.dataclass(frozen=True)
class InstanceDescriptor:
    """Describes an instance of a circuit to be minimized."""

    circuit: Circuit
    source_path: tp.Optional[pathlib.Path]
    metrics: CircuitStats

    @classmethod
    def from_path(cls, path: tp.Union[str, os.PathLike[str]]) -> "InstanceDescriptor":
        path = pathlib.Path(path)
        circuit = Circuit.from_bench_file(path)
        return InstanceDescriptor(
            circuit=circuit,
            source_path=path,
            metrics=CircuitStats.from_circuit(circuit),
        )

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> "InstanceDescriptor":
        return InstanceDescriptor(
            circuit=circuit,
            source_path=None,
            metrics=CircuitStats.from_circuit(circuit),
        )

    def dominates(self, other: "InstanceDescriptor") -> bool:
        return self.metrics.dominates(other.metrics)


class InstanceFrontier(metaclass=abc.ABCMeta):
    def validate_equivalence(self) -> None:
        """Validate that every circuit in the frontier computes the same function."""
        instances = self.get_frontier()
        if not instances:
            raise InvalidFrontierError('The instance frontier must not be empty.')

        reference = instances[0].circuit
        if any(
            not check_circuits_equivalence(reference, instance.circuit)
            for instance in instances[1:]
        ):
            raise InvalidFrontierError(
                'All circuits in the instance frontier must be equivalent.'
            )

    def __str__(self) -> str:
        _metrics = ', '.join(
            str(instance.metrics)
            for instance in sorted(
                self.get_frontier(), key=lambda instance: instance.metrics
            )
        )
        return f"{type(self).__name__}({_metrics})"

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    @abc.abstractmethod
    def read_dir(cls, path: tp.Union[str, os.PathLike[str]]) -> tp_ext.Self:
        """
        Loads all instances from a directory.

        Currently, supports only .bench instances.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def write_dir(
        self,
        path: tp.Union[str, os.PathLike[str]],
        *,
        prefix: str = "",
        remove_existing: bool = False,
    ) -> None:
        """
        Writes the frontier to a directory.

        :param path: The path to the directory to write to.
        :param prefix: The name of the function (prefix for each file name).
        :param remove_existing: Whether to remove existing files in the directory.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def consider_circuit(
        self, new_circuit: tp.Union[Circuit, os.PathLike[str]]
    ) -> bool:
        """
        Considers a new circuit for the front.

        As a result, this method may:
        1. Add a new instance to the front if it is not dominated by any
           existing instance or dominates some instances.
        2. Remove instances from the front if they are dominated by the new instance.
        3. Do nothing if the new instance is dominated by some existing instance.

        Note that this method doesn't validate that the new instance implements
        the same function as old ones.

        :return: True iff the new instance was added to the front.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_frontier(self) -> tp.Sequence[InstanceDescriptor]:
        """
        :return: The sequence of instances that are currently in the front.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_smallest(self) -> InstanceDescriptor:
        """
        :return: The smallest (by size) circuit in the frontier.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_shallowest(self) -> InstanceDescriptor:
        """
        :return: The shallowest (by depth) circuit in the frontier.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def some_instance(self, rng: random.Random) -> InstanceDescriptor:
        """
        :return: Some instance that is currently in the front.

        Note: may or may not be random.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __len__(self) -> int:
        """
        :return: Number of instances in the front.

        """
        raise NotImplementedError


class ParetoFrontier(InstanceFrontier):
    @classmethod
    def read_dir(cls, path: tp.Union[str, os.PathLike[str]]) -> tp_ext.Self:
        path = pathlib.Path(path)
        return cls(sorted(path.glob("*.bench")))

    def __init__(
        self,
        circuits: tp.Sequence[tp.Union[Circuit, pathlib.Path]],
    ):
        self.instances: tp.List[InstanceDescriptor] = []
        for ckt in circuits:
            self.consider_circuit(ckt)

    def write_dir(
        self,
        path: tp.Union[str, os.PathLike[str]],
        *,
        prefix: str = "",
        remove_existing: bool = False,
    ) -> None:
        output_dir = pathlib.Path(path)
        if output_dir.exists():
            if not remove_existing:
                raise ValueError(f"Directory {output_dir} already exists")
            shutil.rmtree(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        _prefix = f"{prefix}_" if prefix else ""
        for descriptor in self.get_frontier():
            output_path = output_dir / (
                f"{_prefix}size_{descriptor.metrics.size}"
                f"_depth_{descriptor.metrics.depth}.bench"
            )
            descriptor.circuit.save_to_file(output_path)

        print(f"Saved frontier to {output_dir}")

    def consider_circuit(
        self, new_circuit: tp.Union[Circuit, str, os.PathLike[str]]
    ) -> bool:
        if isinstance(new_circuit, Circuit):
            new_instance = InstanceDescriptor.from_circuit(new_circuit)
        elif isinstance(new_circuit, (str, os.PathLike)):
            new_instance = InstanceDescriptor.from_path(new_circuit)
        else:
            raise TypeError(
                f"Expected Circuit or pathlib.Path, got {type(new_circuit)}"
            )

        for instance in self.instances:
            if instance.dominates(new_instance):
                return False
            if instance.metrics == new_instance.metrics:
                return False

        self.instances = [
            instance
            for instance in self.instances
            if not new_instance.dominates(instance)
        ]
        self.instances.append(
            new_instance,
        )
        return True

    def get_frontier(self) -> tp.Sequence[InstanceDescriptor]:
        return tuple(self.instances)

    def get_smallest(self) -> InstanceDescriptor:
        return min(self.instances, key=lambda instance: instance.metrics.size)

    def get_shallowest(self) -> InstanceDescriptor:
        return min(self.instances, key=lambda instance: instance.metrics.depth)

    def some_instance(self, rng: random.Random) -> InstanceDescriptor:
        return self.instances[0]

    def __len__(self) -> int:
        return len(self.instances)
