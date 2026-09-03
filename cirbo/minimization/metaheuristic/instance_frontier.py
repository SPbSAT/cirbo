import abc
import dataclasses
import pathlib
import random
import typing as tp

from cirbo.core import Circuit
from cirbo.sat.sat import check_circuits_equivalence
from .exceptions import InvalidFrontierError

__all__ = [
    'CircuitMetrics',
    'InstanceDescriptor',
    'InstanceFrontier',
    'ParetoFrontier',
]


@dataclasses.dataclass(frozen=True, order=True)
class CircuitMetrics:
    """Objective values used by the built-in Pareto search."""

    size: int
    depth: int

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> "CircuitMetrics":
        """Measure gate count and the longest non-input gate path to an output."""
        return CircuitMetrics(size=circuit.gates_number(), depth=circuit.get_depth())

    def dominates(self, other: "CircuitMetrics") -> bool:
        """Return True if self dominates other."""
        return self.size <= other.size and self.depth <= other.depth and self != other

    def __str__(self) -> str:
        return f"(size={self.size}, depth={self.depth})"


@dataclasses.dataclass(frozen=True)
class InstanceDescriptor:
    """Describes an instance of a circuit to be minimized."""

    circuit: Circuit
    source_path: tp.Optional[pathlib.Path]
    metrics: CircuitMetrics

    @classmethod
    def from_path(cls, path: pathlib.Path) -> "InstanceDescriptor":
        circuit = Circuit.from_bench_file(path)
        return InstanceDescriptor(
            circuit=circuit,
            source_path=path,
            metrics=CircuitMetrics.from_circuit(circuit),
        )

    @classmethod
    def from_circuit(cls, circuit: Circuit) -> "InstanceDescriptor":
        return InstanceDescriptor(
            circuit=circuit,
            source_path=None,
            metrics=CircuitMetrics.from_circuit(circuit),
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
        _metrics = ', '.join(str(instance.metrics) for instance in self.get_frontier())
        return f"{type(self).__name__}({_metrics})"

    @abc.abstractmethod
    def consider_circuit(self, new_circuit: Circuit) -> bool:
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
    def any_instance(self, rng: random.Random) -> InstanceDescriptor:
        """
        :return: Any instance that is currently in the front.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def __len__(self) -> int:
        """
        :return: Number of instances in the front.

        """
        raise NotImplementedError


class ParetoFrontier(InstanceFrontier):
    def __init__(
        self,
        circuits: tp.Sequence[Circuit],
    ):
        self.instances: tp.List[InstanceDescriptor] = []
        for ckt in circuits:
            self.consider_circuit(ckt)

    def consider_circuit(self, new_circuit: Circuit) -> bool:
        new_instance = InstanceDescriptor.from_circuit(new_circuit)
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

    def any_instance(self, rng: random.Random) -> InstanceDescriptor:
        return self.instances[0]

    def __len__(self) -> int:
        return len(self.instances)
