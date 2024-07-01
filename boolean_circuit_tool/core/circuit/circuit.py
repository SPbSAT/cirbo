"""Module contains implementation of Circuit class."""

import logging
import pathlib
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.circuit.gate import Gate, GateLabel, GateType
from boolean_circuit_tool.core.circuit.operators import and_, GateState, Undefined
from boolean_circuit_tool.core.circuit.validation import (
    check_gate_lable_doesnt_exist,
    check_gates_exist,
)

logger = logging.getLogger(__name__)

__all__ = ['Circuit']


class Circuit:
    """
    Structure to carry boolean circuit.

    Boolean circuit is represented as a set of Gate objects and
    relations between them.

    Circuit may be constructed manually, gate by gate, using methods
    `add_gate` and `emplace_gate`, or can be parsed from .bench file
    using static method `from_bench`.

    TODO: Circuit also implements BooleanFunction protocol, allowing
    it to be used as boolean function and providing related checks.
    TODO def draw
    TODO def top_sort

    """

    @staticmethod
    def from_bench(stream: tp.Iterable[str]) -> "Circuit":
        """
        Initialization the circuit with given data.

        :param filepath: path to the file with the circuit

        """
        from boolean_circuit_tool.core.parser.bench import BenchToCircuit

        _parser = BenchToCircuit()
        return _parser.convert_to_circuit(stream)

    def __init__(self):
        self.input_gates: set[GateLabel] = set()
        self.output_gates: set[GateLabel] = set()
        self.gates: dict[GateLabel, Gate] = {}

    @property
    def inputs(self) -> set[GateLabel]:
        """Return set of inputs."""
        return self.input_gates

    @property
    def outputs(self) -> set[GateLabel]:
        """Return set of outpus."""
        return self.output_gates

    @property
    def gates_number(self):
        """Return number of gates."""
        return len(self.gates)

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit.

        :param: gate
        :return: circuit with new gate

        """
        check_gate_lable_doesnt_exist(gate.label, self)
        check_gates_exist(tuple(gate.operands), self)
        self.gates[gate.label] = gate
        if gate.gate_type == GateType.INPUT:
            self.input_gates.add(gate.label)

        return self

    def emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit.

        :mandatory param label: new gate's label :mandatory param gate_type: new gate's
        type of operator :mandatory param operands: new gate's operands :optional params
        **kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        check_gate_lable_doesnt_exist(label, self)
        check_gates_exist(operands, self)
        self.gates[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == GateType.INPUT:
            self.input_gates.add(label)

        return self

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings.

        :param: gate
        :return: circuit with new gate

        """
        self.gates[gate.label] = gate
        if gate.gate_type == GateType.INPUT:
            self.input_gates.add(gate.label)

        return self

    def _emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings.

        :mandatory param label: new gate's label :mandatory param gate_type: new gate's
        type of operator :mandatory param operands: new gate's operands :optional params
        **kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        self.gates[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == GateType.INPUT:
            self.input_gates.add(label)

        return self

    def rename_gate(self, old_label: GateLabel, new_label: GateLabel) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace
        :param new_label: gate's new label
        :return: modified circuit

        """
        if old_label in self.input_gates:
            self.input_gates.remove(old_label)
            self.input_gates.add(new_label)

        new_gates = {}
        for gate_label, gate in self.gates.items():
            if gate_label == old_label:
                new_gates[new_label] = Gate(
                    new_label, gate.gate_type, tuple(gate.operands)
                )
            elif old_label in list(gate.operands):
                new_gates[gate_label] = Gate(
                    gate.label,
                    gate.gate_type,
                    tuple(
                        new_label if oper == old_label else oper
                        for oper in gate.operands
                    ),
                )
            else:
                new_gates[gate_label] = self.gates[gate_label]
        self.gates = new_gates

        if old_label in self.output_gates:
            self.output_gates.remove(old_label)
            self.output_gates.add(new_label)

        return self

    def mark_as_output(self, label: GateLabel) -> None:
        check_gates_exist((label,), self)
        self.output_gates.add(label)

    def evaluate_circuit(
        self,
        assigment: dict[str, GateState],
    ) -> GateState:  # или мы хотим вектор значений выходов схемы
        """
        Evaluate the circuit with the given input values.

        :param assigment: assigment for inputs

        """

        assigment_dict = dict()
        for input in self.input_gates:
            assigment_dict[input] = (
                assigment[input] if input in assigment else Undefined
            )

        queue_ = list()

        for output in self.output_gates:
            queue_.append(self.gates[output])

        for gate in queue_:
            for operand in gate.operands:
                queue_.append(self.gates[operand])

        for gate in reversed(queue_):
            if gate.label not in assigment_dict:
                assigment_dict[gate.label] = gate.operator(
                    *[assigment_dict[op] for op in gate.operands]
                )

        return and_(True, *[assigment_dict[output] for output in self.output_gates])

    def save_to_file(self, path: str) -> None:
        """
        Save circuit to file.

        :param path: path to file with file's name and file's extention

        """
        p = pathlib.Path(path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=False)
        p.write_text(str(self))

    def __str__(self):
        input_str = '\n'.join(
            f'INPUT({input_label})' for input_label in self.input_gates
        )
        gates_str = '\n'.join(
            str(gate)
            for gate in self.gates.values()
            if gate.gate_type != GateType.INPUT
        )
        output_str = '\n'.join(
            f'OUTPUT({output_label})' for output_label in self.output_gates
        )

        return f"{input_str}\n\n{gates_str}\n\n{output_str}"
