"""Module contains implementation of Circuit class."""

import collections
import itertools
import logging
import pathlib
import textwrap
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.boolean_function import BooleanFunction
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitElementAlreadyExistsError,
    CircuitElementIsAbsentError,
)
from boolean_circuit_tool.core.circuit.gate import Gate, GateType, INPUT, Label
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.validation import (
    check_elements_exist,
    check_label_doesnt_exist,
)


logger = logging.getLogger(__name__)

__all__ = ['Circuit']


class Circuit(BooleanFunction):
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

    def __init__(self):
        self._inputs: list[Label] = list()
        self._outputs: list[Label] = list()
        self._elements: dict[Label, Gate] = {}
        self._element_to_users: tp.DefaultDict[Label, list[Label]] = (
            collections.defaultdict(list)
        )

    @property
    def inputs(self) -> list[Label]:
        """
        :return: list of inputs.

        """
        return self._inputs

    @property
    def input_size(self) -> int:
        """
        :return: number of inputs.

        """
        return len(self._inputs)

    @property
    def outputs(self) -> list[Label]:
        """
        :return: list of outputs.

        """
        return self._outputs

    @property
    def output_size(self) -> int:
        """
        :return: number of outputs.

        """
        return len(self._outputs)

    @property
    def elements_number(self) -> int:
        """
        :return: number of elements into the circuit.

        """
        return len(self._elements)

    def get_element(self, label: Label) -> Gate:
        """
        :return: a specific element from the schema by `label`.

        """
        return self._elements[label]

    def get_element_users(self, label: Label) -> list[Label]:
        """
        :return: list of gates which use given gate as operand.

        """
        return self._element_to_users[label]

    def has_element(self, label: Label) -> bool:
        """
        :return: True iff this circuit has element `label`.

        """
        return label in self._elements

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param gate: new gate.
        :return: modified circuit.

        """
        check_label_doesnt_exist(gate.label, self)
        check_elements_exist(gate.operands, self)

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

        :param label: new gate's label.
        :param gate_type: new gate's type of operator.
        :param operands: new gate's operands.
        :param kwargs: others parameters for conctructing new gate.
        :return: modified circuit.

        """
        check_label_doesnt_exist(label, self)
        check_elements_exist(operands, self)

        return self._emplace_gate(label, gate_type, operands, **kwargs)

    def rename_element(self, old_label: Label, new_label: Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace.
        :param new_label: gate's new label.
        :return: modified circuit.

        """
        if old_label not in self._elements:
            raise CircuitElementIsAbsentError()

        if new_label in self._elements:
            raise CircuitElementAlreadyExistsError()

        if old_label in self._inputs:
            self._inputs.remove(old_label)
            self._inputs.append(new_label)

        if old_label in self._outputs:
            self._outputs.remove(old_label)
            self._outputs.append(new_label)

        self._elements[new_label] = Gate(
            new_label,
            self._elements[old_label].gate_type,
            self._elements[old_label].operands,
        )

        self._element_to_users[new_label] = self._element_to_users[old_label]

        for user_label in self._element_to_users[old_label]:
            self._elements[user_label] = Gate(
                user_label,
                self._elements[user_label].gate_type,
                tuple(
                    new_label if oper == old_label else oper
                    for oper in self._elements[user_label].operands
                ),
            )

        for operand_label in self._elements[old_label].operands:
            operand_users = self._element_to_users[operand_label]
            assert old_label in operand_users
            operand_users[operand_users.index(old_label)] = new_label

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

        Create a new list by copying `inputs` and then appending to it the
        elements of `self._inputs` that are not already in the resulting list.
        After that replaces `self._inputs` with this new list.

        :param inputs: full or partially sorted list of inputs.
        :return: modified circuit.

        """
        self._inputs = _sort_list(inputs, self._inputs)
        return self

    def sort_outputs(self, outputs: list[Label]) -> tp_ext.Self:
        """
        Sort output gates.

        Create a new list by copying `inputs` and then appending to it the
        elements of `self._inputs` that are not already in the resulting list.
        After that replaces `self._inputs` with this new list.

        :param outputs: full or partially sorted list of outputs.
        :return: modified circuit.

        """
        self._outputs = _sort_list(outputs, self._outputs)
        return self

    def evaluate_circuit(
        self,
        assigment: dict[str, GateState],
    ) -> dict[str, GateState]:
        """
        Evaluate the circuit with the given input values.

        :param assigment: full or partually assigment for inputs.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any element of the circuit.

        """

        assigment_dict: dict[str, GateState] = dict(assigment)
        for input in self._inputs:
            assigment_dict.setdefault(input, Undefined)

        queue_: list[Label] = list()

        for output in self._outputs:
            if output not in self._inputs:
                queue_.append(output)

        while queue_:
            gate = self.get_element(queue_[-1])

            for operand in gate.operands:
                if operand not in assigment_dict:
                    queue_.append(operand)

            if gate.label == queue_[-1]:
                assigment_dict[gate.label] = gate.operator(
                    *(assigment_dict[op] for op in gate.operands)
                )
                queue_.pop()

        return {output: assigment_dict[output] for output in self._outputs}

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        dict_inputs = {}
        for i, input in enumerate(self._inputs):
            dict_inputs[input] = inputs[i]

        return list(self.evaluate_circuit(dict_inputs).values())

    def evaluate_at(self, inputs: list[bool], output_index: int) -> bool:
        """
        Get value of `output_index`th output that corresponds to provided `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        return self.evaluate(inputs)[output_index]

    def is_constant(self) -> bool:
        """
        Check if all outputs are constant (input independent).

        :return: True iff this function is constant.

        """
        answer: list[GateState] = self.evaluate([0] * self.input_size)
        for x in itertools.product((0, 1), repeat=self.input_size):
            if answer != self.evaluate(list(x)):
                return False
        return True

    def is_constant_at(self, output_index: int) -> bool:
        """
        Check if output `output_index` is constant (input independent).

        :param output_index: index of desired output.
        :return: True iff output `output_index` is constant.

        """
        answer: GateState = self.evaluate_at([0] * self.input_size, output_index)
        for x in itertools.product((0, 1), repeat=self.input_size):
            if answer != self.evaluate_at(list(x), output_index):
                return False
        return True

    def is_monotonic(self, *, inverse: bool) -> bool:
        """
        Check if all outputs are monotonic (output value doesn't decrease when
        inputs are enumerated in a classic order: 0000, 0001, 0010, 0011 ...).

        :param inverse: if True, will check that output values doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff this function is monotonic.

        """
        change_value: list[GateState] = [False] * self.output_size
        current_value: list[bool] = [inverse] * self.output_size
        for x in itertools.product((0, 1), repeat=self.input_size):
            for i, v in enumerate(self.evaluate(list(x))):
                if v != current_value[i]:
                    if change_value[i]:
                        return False
                    change_value[i] = True
                    current_value[i] = not current_value[i]
        return True

    def is_monotonic_at(self, output_index: int, *, inverse: bool) -> bool:
        """
        Check if output `output_index` is monotonic (output value doesn't
        decrease when inputs are enumerated in a classic order: 0000, 0001,
        0010, 0011 ...).

        :param output_index: index of desired output.
        :param inverse: if True, will check that output value doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff output `output_index` is monotonic.

        """
        change_value: bool = False
        current_value: bool = inverse
        for x in itertools.product((0, 1), repeat=self.input_size):
            if self.evaluate_at(list(x), output_index) != current_value:
                if change_value:
                    return False
                change_value = True
                current_value = not current_value
        return True

    def is_symmetric(self) -> bool:
        """
        Check if all outputs are symmetric.

        :return: True iff this function.

        """

    def is_symmetric_at(self, output_index: int) -> bool:
        """
        Check that output `output_index` is symmetric.

        :param output_index: index of desired output.
        :return: True iff output `output_index` is symmetric.

        """

    def is_dependent_on_input_at(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` depends on input `input_index` (there exist two
        input sets that differ only at `input_index`, but result in different value for
        `output_index`).

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` depends on input `input_index`.

        """

    def is_output_equal_to_input(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` equals to input `input_index`.

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` equals to the input
        `input_index`.

        """

    def is_output_equal_to_input_negation(
        self,
        output_index: int,
        input_index: int,
    ) -> bool:
        """
        Check if output `output_index` equals to negation of input `input_index`.

        :param output_index: index of desired output.
        :param input_index: index of desired input.
        :return: True iff output `output_index` equals to negation of input
        `input_index`.

        """

    def get_significant_inputs_of(self, output_index: int) -> list[int]:
        """
        Get indexes of all inputs on which output `output_index` depends on.

        :param output_index: index of desired output.
        :return: list of input indices.

        """

    def get_symmetric_and_negations_of(
        self,
        output_index: list[int],
    ) -> tp.Optional[list[bool]]:
        """
        Check if function is symmetric on some output set and returns inputs negations.

        :param output_index: output index set

        """

    def get_truth_table(self) -> list[list[bool]]:
        """
        Get truth table of a boolean function, which is a matrix, `i`th row of which
        contains values of `i`th output, and `j`th column corresponds to the input which
        is a binary encoding of a number `j` (for example j=9 corresponds to [..., 1, 0,
        0, 1])

        :return: truth table describing this function.

        """
        return [
            list(i)
            for i in zip(
                *[
                    self.evaluate(list(x))
                    for x in itertools.product((0, 1), repeat=self.input_size)
                ]
            )
        ]

    def save_to_file(self, path: str) -> None:
        """
        Save circuit to file.

        :param path: path to file with file's name and file's extention.

        """
        p = pathlib.Path(path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=False)
        p.write_text(self.format_circuit())

    def format_circuit(self) -> str:
        """Formats circuit as string in BENCH format."""

        input_str = '\n'.join(f'INPUT({input_label})' for input_label in self._inputs)
        gates_str = '\n'.join(
            gate.format_gate()
            for gate in self._elements.values()
            if gate.gate_type != INPUT
        )
        output_str = '\n'.join(
            f'OUTPUT({output_label})' for output_label in self._outputs
        )
        return f"{input_str}\n\n{gates_str}\n\n{output_str}"

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings (!!!) and without filling users.

        :param: gate.
        :return: circuit with new gate.

        """
        for operand in gate.operands:
            self._add_user(operand, gate.label)

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

        :param label: new gate's label.
        :param gate_type: new gate's type of operator.
        :param operands: new gate's operands.
        :params kwargs: others parameters for conctructing new gate.
        :return: circuit with new gate.

        """
        for operand in operands:
            self._add_user(operand, label)

        self._elements[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == INPUT:
            self._inputs.append(label)

        return self

    def _add_user(self, element: Label, user: Label):
        """Adds user for `element`."""
        self._element_to_users[element].append(user)

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
        return f"{self.__class__.__name__}\n\t{input_str}\n\t{output_str}"


def _sort_list(
    sorted_list: list[Label],
    old_list: list[Label],
) -> list[Label]:
    """
    Sort old elements list with full or partially sorted elements list.

    Creates new list by copying `sorted_list`, then appends to it elements
    of `old_list` which are yet absent in resulting list.

    `sorted_list` must be subset of `old_list`.

    """
    new_list = list()
    for elem in sorted_list:
        if elem not in old_list:
            raise CircuitElementIsAbsentError()
        new_list.append(elem)

    if len(new_list) == len(old_list):
        return new_list

    for elem in old_list:
        if elem not in new_list:
            new_list.append(elem)

    return new_list
