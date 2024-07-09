"""Module contains implementation of Circuit class."""

import logging
import pathlib
import textwrap
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.circuit.gate import Gate, GateLabel, GateType, INPUT
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
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

    def __init__(self, name: str = 'Circuit'):
        self.name = name
        self._input_gates: list[GateLabel] = list()
        self._output_gates: list[GateLabel] = list()
        self._gates: dict[GateLabel, Gate] = {}

    @property
    def inputs(self) -> list[GateLabel]:
        """Return set of inputs."""
        return self._input_gates

    @property
    def outputs(self) -> list[GateLabel]:
        """Return set of outpus."""
        return self._output_gates

    @property
    def gates_number(self) -> int:
        """Return number of gates."""
        return len(self._gates)

    def get_gate(self, label: GateLabel) -> Gate:
        assert label in self._gates
        return self._gates[label]

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param: gate
        :return: circuit with new gate

        """
        check_gate_lable_doesnt_exist(gate.label, self)
        check_gates_exist(tuple(gate.operands), self)

        for operand in gate.operands:
            self.get_gate(operand)._add_users(gate.label)

        return self._add_gate(gate)

    def emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit.

        :param label: new gate's label
        :param gate_type: new gate's type of operator
        :param operands: new gate's operands
        :param kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        check_gate_lable_doesnt_exist(label, self)
        check_gates_exist(operands, self)

        for operand in operands:
            self.get_gate(operand)._add_users(label)

        return self._emplace_gate(label, gate_type, operands, **kwargs)

    def rename_gate(self, old_label: GateLabel, new_label: GateLabel) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace
        :param new_label: gate's new label
        :return: modified circuit

        """
        if old_label not in self._gates:
            return self

        if old_label in self._input_gates:
            self._input_gates.remove(old_label)
            self._input_gates.append(new_label)

        self._gates[new_label] = Gate(
            new_label,
            self._gates[old_label].gate_type,
            tuple(self._gates[old_label].operands),
        )

        for user_label in self._gates[old_label].users:
            self._gates[user_label] = Gate(
                user_label,
                self._gates[user_label].gate_type,
                tuple(
                    new_label if oper == old_label else oper
                    for oper in self._gates[user_label].operands
                ),
            )
            self._gates[new_label]._add_users(user_label)

        if old_label in self._output_gates:
            self._output_gates.remove(old_label)
            self._output_gates.append(new_label)

        del self._gates[old_label]
        return self

    def mark_as_output(self, label: GateLabel) -> None:
        """Mark as output a gate."""
        if label not in self._output_gates:
            check_gates_exist((label,), self)
            self._output_gates.append(label)

    def sort_inputs(self, inputs: list[GateLabel]) -> tp_ext.Self:
        """
        Sort input gates.

        :param inputs: sorted (maybe partially) list of inputs
        :return: circuit with sorted inputs

        """
        self._input_gates = _sort_gates(inputs, self._input_gates)
        return self

    def sort_outputs(self, outputs: list[GateLabel]) -> tp_ext.Self:
        """
        Sort output gates.

        :param outputs: sorted (maybe partially) list of outputs
        :return: circuit with sorted outputs

        """
        self._output_gates = _sort_gates(outputs, self._output_gates)
        return self

    def evaluate(
        self,
        assigment: dict[str, GateState],
    ) -> dict[str, GateState]:
        """
        Evaluate the circuit with the given input values.

        :param assigment: assigment for inputs
        :return: outputs dictionary with the obtained values

        """

        assigment_dict: dict[str, GateState] = dict()
        for input in self._input_gates:
            assigment_dict[input] = assigment.get(input, Undefined)

        queue_: list[Gate] = list()

        for output in self._output_gates:
            if output not in self._input_gates:
                queue_.append(self._gates[output])

        while queue_:
            gate = queue_[-1]

            for operand in gate.operands:
                if operand not in assigment_dict:
                    queue_.append(self._gates[operand])

            if gate == queue_[-1]:
                assigment_dict[gate.label] = gate.operator(
                    *(assigment_dict[op] for op in gate.operands)
                )
                queue_.pop()

        return {output: assigment_dict[output] for output in self._output_gates}

    def save_to_file(self, path: str) -> None:
        """
        Save circuit to file.

        :param path: path to file with file's name and file's extention

        """
        p = pathlib.Path(path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=False)
        p.write_text(self.print_circuit())

    def print_circuit(self) -> str:
        input_str = '\n'.join(
            f'INPUT({input_label})' for input_label in self._input_gates
        )
        gates_str = '\n'.join(
            str(gate) for gate in self._gates.values() if gate.gate_type != INPUT
        )
        output_str = '\n'.join(
            f'OUTPUT({output_label})' for output_label in self._output_gates
        )
        return f"{input_str}\n\n{gates_str}\n\n{output_str}"

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings (!!!) and without filling users.

        :param: gate
        :return: circuit with new gate

        """
        self._gates[gate.label] = gate
        if gate.gate_type == INPUT:
            self._input_gates.append(gate.label)

        return self

    def _emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tuple[GateLabel, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings (!!!) and without filling users.

        :param label: new gate's label
        :param gate_type: new gate's type of operator
        :param operands: new gate's operands
        :params kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        self._gates[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == INPUT:
            self._input_gates.append(label)

        return self

    def __str__(self):
        input_str = textwrap.shorten(
            'INPUTS: '
            + '; '.join(f'{input_label}' for input_label in self._input_gates),
            wigth=100,
        )
        output_str = textwrap.shorten(
            'OUTPUTS: '
            + '; '.join(f'{output_label}' for output_label in self._output_gates),
            wigth=100,
        )
        return f"{self.name}\n{input_str}\n{output_str}"


def _sort_gates(
    sorted_gates_list: list[GateLabel],
    old_gates_list: list[GateLabel],
) -> list[GateLabel]:
    """Sort old gates list with full or partially sorted gates list."""

    new_gates_list = list()
    for gate in sorted_gates_list:
        assert gate in old_gates_list
        new_gates_list.append(gate)

    if len(new_gates_list) != len(old_gates_list):
        for input in old_gates_list:
            if input not in new_gates_list:
                new_gates_list.append(input)

    return new_gates_list
