"""Module contains implementation of Circuit class."""

import logging
import pathlib
import textwrap
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.circuit.gate import Gate, GateType, INPUT, Label
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.validation import (
    check_elements_exist,
    check_label_doesnt_exist,
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
        self._inputs: list[Label] = list()
        self._outputs: list[Label] = list()
        self._elements: dict[Label, Gate] = {}

    @property
    def inputs(self) -> list[Label]:
        """Return set of inputs."""
        return self._inputs

    @property
    def outputs(self) -> list[Label]:
        """Return set of outpus."""
        return self._outputs

    @property
    def elements_number(self) -> int:
        """Return number of elements."""
        return len(self._elements)

    def get_element(self, label: Label) -> Gate:
        assert label in self._elements
        return self._elements[label]

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param: gate
        :return: circuit with new gate

        """
        check_label_doesnt_exist(gate.label, self)
        check_elements_exist(tuple(gate.operands), self)

        for operand in gate.operands:
            self.get_element(operand)._add_users(gate.label)

        return self._add_gate(gate)

    def emplace_gate(
        self,
        label: Label,
        gate_type: GateType,
        operands: tuple[Label, ...] = (),
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
        check_label_doesnt_exist(label, self)
        check_elements_exist(operands, self)

        for operand in operands:
            self.get_element(operand)._add_users(label)

        return self._emplace_gate(label, gate_type, operands, **kwargs)

    def rename_element(self, old_label: Label, new_label: Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace
        :param new_label: gate's new label
        :return: modified circuit

        """
        if old_label not in self._elements:
            return self  # assert ?

        if old_label in self._inputs:
            self._inputs.remove(old_label)
            self._inputs.append(new_label)

        self._elements[new_label] = Gate(
            new_label,
            self._elements[old_label].gate_type,
            tuple(self._elements[old_label].operands),
        )

        for user_label in self._elements[old_label].users:
            self._elements[user_label] = Gate(
                user_label,
                self._elements[user_label].gate_type,
                tuple(
                    new_label if oper == old_label else oper
                    for oper in self._elements[user_label].operands
                ),
            )
            self._elements[new_label]._add_users(user_label)

        if old_label in self._outputs:
            self._outputs.remove(old_label)
            self._outputs.append(new_label)

        del self._elements[old_label]
        return self

    def mark_as_output(self, label: Label) -> None:
        """Mark as output a gate."""
        if label not in self._outputs:
            check_elements_exist((label,), self)
            self._outputs.append(label)

    def sort_inputs(self, inputs: list[Label]) -> tp_ext.Self:
        """
        Sort input gates.

        :param inputs: sorted (maybe partially) list of inputs
        :return: circuit with sorted inputs

        """
        self._inputs = _sort_list(inputs, self._inputs)
        return self

    def sort_outputs(self, outputs: list[Label]) -> tp_ext.Self:
        """
        Sort output gates.

        :param outputs: sorted (maybe partially) list of outputs
        :return: circuit with sorted outputs

        """
        self._outputs = _sort_list(outputs, self._outputs)
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
        for input in self._inputs:
            assigment_dict[input] = assigment.get(input, Undefined)

        queue_: list[Gate] = list()

        for output in self._outputs:
            if output not in self._inputs:
                queue_.append(self._elements[output])

        while queue_:
            gate = queue_[-1]

            for operand in gate.operands:
                if operand not in assigment_dict:
                    queue_.append(self._elements[operand])

            if gate == queue_[-1]:
                assigment_dict[gate.label] = gate.operator(
                    *(assigment_dict[op] for op in gate.operands)
                )
                queue_.pop()

        return {output: assigment_dict[output] for output in self._outputs}

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
        input_str = '\n'.join(f'INPUT({input_label})' for input_label in self._inputs)
        gates_str = '\n'.join(
            str(gate) for gate in self._elements.values() if gate.gate_type != INPUT
        )
        output_str = '\n'.join(
            f'OUTPUT({output_label})' for output_label in self._outputs
        )
        return f"{input_str}\n\n{gates_str}\n\n{output_str}"

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings (!!!) and without filling users.

        :param: gate
        :return: circuit with new gate

        """
        self._elements[gate.label] = gate
        if gate.gate_type == INPUT:
            self._inputs.append(gate.label)

        return self

    def _emplace_gate(
        self,
        label: Label,
        gate_type: GateType,
        operands: tuple[Label, ...] = (),
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
        self._elements[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == INPUT:
            self._inputs.append(label)

        return self

    def __str__(self):
        input_str = textwrap.shorten(
            'INPUTS: ' + '; '.join(f'{input_label}' for input_label in self._inputs),
            wigth=100,
        )
        output_str = textwrap.shorten(
            'OUTPUTS: '
            + '; '.join(f'{output_label}' for output_label in self._outputs),
            wigth=100,
        )
        return f"{self.name}\n{input_str}\n{output_str}"


def _sort_list(
    sorted_list: list[Label],
    old_list: list[Label],
) -> list[Label]:
    """Sort old elements list with full or partially sorted elements list."""

    new_list = list()
    for elem in sorted_list:
        assert elem in old_list
        new_list.append(elem)

    if len(new_list) != len(old_list):
        for elem in old_list:
            if elem not in new_list:
                new_list.append(elem)

    return new_list
