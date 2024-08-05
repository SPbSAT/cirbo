"""Module contains implementation of Circuit class."""

import collections
import itertools
import logging
import pathlib
import textwrap
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.boolean_function import BooleanFunction, RawTruthTable
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitElementAlreadyExistsError,
    CircuitElementIsAbsentError,
    CircuitIsCyclicalError,
)
from boolean_circuit_tool.core.circuit.gate import Gate, GateType, INPUT, Label
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.utils import (
    input_iterator_with_fixed_sum,
    order_list,
)
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

    """

    @staticmethod
    def from_bench(file_path: str) -> "Circuit":
        """
        Initialization the circuit with given data.

        :param filepath: path to the file with the circuit

        """
        from boolean_circuit_tool.core.parser.bench import BenchToCircuit

        _parser = BenchToCircuit()

        path = pathlib.Path(file_path)
        with path.open() as file:
            return _parser.convert_to_circuit(file)

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
    def elements(self) -> dict[Label, Gate]:
        """
        :return: dict of elements into the circuit.

        """
        return self._elements

    @property
    def elements_number(self) -> int:
        """
        :return: number of elements into the circuit.

        """
        return len(self._elements)

    def input_at_index(self, idx: int) -> Label:
        """
        :param idx: input index
        :return: inputs label which corresponds to the index

        """
        return self._inputs[idx]

    def index_of_input(self, label: Label) -> int:
        """
        :param label: input label
        :return: inputs index which corresponds to the label

        """
        return self._inputs.index(label)

    def output_at_index(self, idx: int) -> Label:
        """
        :param idx: output index
        :return: outputs label which corresponds to the index

        """
        return self._outputs[idx]

    def index_of_output(self, label: Label) -> int:
        """
        :param idx: output label
        :return: first outputs index which corresponds to the label

        """
        return self._outputs.index(label)

    def all_indexes_of_output(self, label: Label) -> list[int]:
        """
        :param idx: output label
        :return: all outputs indexes which corresponds to the label

        """
        return [idx for idx, output in enumerate(self._outputs) if output == label]

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
    
    def remove_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Remove gate from the circuit.

        :param gate: gate to remove.
        :return: modified circuit.

        """
        check_elements_exist((gate.label,), self)
        # check_elements_exist(gate.operands, self)

        return self._remove_gate(gate)

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
    
    def replace_subcircuit(
        self,
        subcircuit: tp_ext.Self,
        inputs_mapping: dict[Label, Label],
        outputs_mapping: dict[Label, Label]
    ) -> tp_ext.Self:
        labels_to_remove = []
        label_is_visited = collections.defaultdict(bool)
        for output_label in outputs_mapping:
            queue = collections.deque()
            if not label_is_visited[output_label]:
                label_is_visited[output_label]
                queue.append(output_label)
            while queue:
                label = queue.popleft()
                if label not in inputs_mapping and label not in outputs_mapping:
                    labels_to_remove.append(label)
                if label not in inputs_mapping:
                    for operand in self.get_element(label).operands:
                        if not label_is_visited[operand]:
                            label_is_visited[operand] = True
                            queue.append(operand)
                            if label in outputs_mapping and (operand in inputs_mapping or operand in outputs_mapping):
                                self._remove_user(operand, label)
        for label in labels_to_remove:
            self._remove_gate(self.get_element(label))
        for label1, label2 in inputs_mapping.items():
            subcircuit.rename_element(old_label=label2, new_label=label1)
        for label1, label2 in outputs_mapping.items():
            subcircuit.rename_element(old_label=label2, new_label=label1)
        for node in subcircuit.top_sort(inversed=True):
            label = node.label
            if label not in inputs_mapping and label not in outputs_mapping:
                self.add_gate(subcircuit.get_element(label))
        for label in outputs_mapping:
            self.get_element(label)._operands = subcircuit.get_element(label)._operands
            self.get_element(label)._gate_type = subcircuit.get_element(label)._gate_type
            for operand in self.get_element(label)._operands:
                if operand in inputs_mapping or operand in outputs_mapping:
                    self._add_user(operand, label)
        return self            


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
            self._inputs[self.index_of_input(old_label)] = new_label

        for idx in self.all_indexes_of_output(old_label):
            self._outputs[idx] = new_label

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
        """Mark as output a gate and append it to the end of `self._outputs`."""
        check_elements_exist((label,), self)
        self._outputs.append(label)

    def order_inputs(self, inputs: list[Label]) -> tp_ext.Self:
        """
        Order input gates.

        Create a new list by copying `inputs` and then appending to it the
        elements of `self._inputs` that are not already in the resulting list.
        After that replaces `self._inputs` with this new list.

        :param inputs: full or partially ordered list of inputs.
        :return: modified circuit.

        """
        self._inputs = order_list(inputs, self._inputs)
        return self

    def order_outputs(self, outputs: list[Label]) -> tp_ext.Self:
        """
        Order output gates.

        Create a new list by copying `outputs` and then appending to it the
        elements of `self._outputs` that are not already in the resulting list.
        After that replaces `self._outputs` with this new list.

        :param outputs: full or partially ordered list of outputs.
        :return: modified circuit.

        """
        self._outputs = order_list(outputs, self._outputs)
        return self

    def top_sort(self, *, inversed: bool = False) -> tp.Iterable[Gate]:
        """
        :param inversed: a boolean value specifying the sort order.
            If inversed == True, Iterator will start from inputs, otherwise from outputs.
        :return: Iterator of gates, which sorted in topological order according Kana algorithm.

        """

        if self.elements_number == 0:
            return

        _predecessors_getter = (
            (lambda elem: len(elem.operands))
            if inversed
            else (lambda elem: len(self.get_element_users(elem.label)))
        )

        _successors_getter = (
            (lambda elem: self.get_element_users(elem.label))
            if inversed
            else (lambda elem: elem.operands)
        )

        indegree_map: dict[Label, int] = {
            elem.label: _predecessors_getter(elem) for elem in self._elements.values()
        }

        queue: list[Label] = [
            label for label, value in indegree_map.items() if value == 0
        ]

        if not queue:
            raise CircuitIsCyclicalError()

        while queue:
            current_elem = self.get_element(queue.pop())
            for succ in _successors_getter(current_elem):
                indegree_map[succ] -= 1
                if indegree_map[succ] == 0:
                    queue.append(succ)
            yield current_elem

    def evaluate_circuit(
        self,
        assigment: dict[str, GateState],
        *,
        outputs: tp.Optional[list[Label]] = None,
    ) -> dict[str, GateState]:
        """
        Evaluate the circuit with the given input values and return full assigment.

        :param assigment: full or partial assigment for inputs.
        :param outputs: set of outputs which need to be evaluated. Those outputs will
               be used to initialise depth-first iteration across the circuit.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any element of the circuit.

        """

        assigment_dict: dict[str, GateState] = dict(assigment)
        for input in self._inputs:
            assigment_dict.setdefault(input, Undefined)

        queue_: list[Label] = list()

        _outputs = self._outputs if outputs is None else outputs
        for output in _outputs:
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

        for element in self._elements:
            assigment_dict.setdefault(element, Undefined)

        return assigment_dict

    def evaluate_circuit_outputs(
        self,
        assigment: dict[str, GateState],
    ) -> dict[str, GateState]:
        """
        Evaluate the circuit with the given input values and return outputs assigment.

        :param assigment: full or partial assigment for inputs.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any element of the circuit.

        """
        assigment_dict: dict[str, GateState] = self.evaluate_circuit(assigment)

        return {output: assigment_dict[output] for output in self._outputs}

    def evaluate(self, inputs: list[bool]) -> list[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        dict_inputs: dict[str, GateState] = {}
        for i, input in enumerate(self._inputs):
            dict_inputs[input] = inputs[i]

        # because of the complete assignment we know that Undefined will not appear
        return tp.cast(
            list[bool], list(self.evaluate_circuit_outputs(dict_inputs).values())
        )

    def evaluate_at(self, inputs: list[bool], output_index: int) -> bool:
        """
        Get value of `output_index`th output that corresponds to provided `inputs`.

        :param inputs: values of input gates.
        :param output_index: index of desired output.
        :return: value of `output_index` evaluated for input values `inputs`.

        """
        dict_inputs: dict[str, GateState] = {}
        for i, input in enumerate(self._inputs):
            dict_inputs[input] = inputs[i]

        label_output = self.output_at_index(output_index)
        # because of the complete assignment we know that Undefined will not appear
        return tp.cast(
            bool,
            self.evaluate_circuit(dict_inputs, outputs=[label_output])[label_output],
        )

    def is_constant(self) -> bool:
        """
        Check if all outputs are constant (input independent).

        :return: True iff this function is constant.

        """
        _iter = itertools.product((False, True), repeat=self.input_size)
        answer: list[bool] = self.evaluate(list(next(_iter)))
        for input_assignment in _iter:
            if answer != self.evaluate(list(input_assignment)):
                return False
        return True

    def is_constant_at(self, output_index: int) -> bool:
        """
        Check if output `output_index` is constant (input independent).

        :param output_index: index of desired output.
        :return: True iff output `output_index` is constant.

        """
        _iter = itertools.product((False, True), repeat=self.input_size)
        answer: bool = self.evaluate_at(list(next(_iter)), output_index)
        for input_assignment in _iter:
            if answer != self.evaluate_at(list(input_assignment), output_index):
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
        change_value: list[bool] = [False] * self.output_size
        current_value: list[bool] = [inverse] * self.output_size
        for input_assignment in itertools.product(
            (False, True), repeat=self.input_size
        ):
            for i, v in enumerate(self.evaluate(list(input_assignment))):
                if v != current_value[i]:
                    if change_value[i]:
                        return False
                    change_value[i] = True
                    current_value[i] = v
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
        for input_assignment in itertools.product(
            (False, True), repeat=self.input_size
        ):
            if self.evaluate_at(list(input_assignment), output_index) != current_value:
                if change_value:
                    return False
                change_value = True
                current_value = not current_value
        return True

    def is_symmetric(self) -> bool:
        """
        Check if all outputs are symmetric.

        :return: True iff this function is symmetric.

        """
        for number_of_true in range(self.input_size + 1):

            _iter = iter(input_iterator_with_fixed_sum(self.input_size, number_of_true))
            value: list[bool] = self.evaluate(next(_iter))

            for input_assignment in _iter:
                if value != self.evaluate(input_assignment):
                    return False

        return True

    def is_symmetric_at(self, output_index: int) -> bool:
        """
        Check that output `output_index` is symmetric.

        :param output_index: index of desired output.
        :return: True iff output `output_index` is symmetric.

        """
        for number_of_true in range(self.input_size + 1):

            _iter = iter(input_iterator_with_fixed_sum(self.input_size, number_of_true))
            value: GateState = self.evaluate_at(next(_iter), output_index)

            for input_assignment in _iter:
                if value != self.evaluate_at(input_assignment, output_index):
                    return False

        return True

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
        for x in itertools.product((False, True), repeat=self.input_size - 1):
            _x = list(x)
            _x.insert(input_index, False)
            value1 = self.evaluate_at(_x, output_index)
            _x[input_index] = not _x[input_index]
            value2 = self.evaluate_at(_x, output_index)
            if value1 != value2:
                return True
        return False

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
        for x in itertools.product((False, True), repeat=self.input_size):
            if self.evaluate_at(list(x), output_index) != x[input_index]:
                return False
        return True

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
        for x in itertools.product((False, True), repeat=self.input_size):
            if self.evaluate_at(list(x), output_index) != (not x[input_index]):
                return False
        return True

    def get_significant_inputs_of(self, output_index: int) -> list[int]:
        """
        Get indexes of all inputs on which output `output_index` depends on.

        :param output_index: index of desired output.
        :return: list of input indices.  TODO make it more efficient when time comes

        """
        return [
            input_index
            for input_index in range(self.input_size)
            if self.is_dependent_on_input_at(output_index, input_index)
        ]

    def find_negations_to_make_symmetric(
        self,
        output_index: list[int],
    ) -> tp.Optional[list[bool]]:
        """
        Check if function is symmetric on some output set and returns inputs negations.

        :param output_index: output index set

        """

        def _filter_required_outputs(result: tp.Sequence[bool]):
            nonlocal output_index
            return [result[idx] for idx in output_index]

        for negations in itertools.product((False, True), repeat=self.input_size):

            symmetric = True
            for number_of_true in range(self.input_size + 1):

                _iter = iter(
                    input_iterator_with_fixed_sum(
                        self.input_size,
                        number_of_true,
                        negations=list(negations),
                    )
                )
                value: list[GateState] = _filter_required_outputs(
                    self.evaluate(next(_iter))
                )

                for input_assignment in _iter:
                    if value != _filter_required_outputs(
                        self.evaluate(input_assignment)
                    ):
                        symmetric = False
                        break

                if not symmetric:
                    break

            if symmetric:
                return list(negations)

        return None

    def get_truth_table(self) -> RawTruthTable:
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
                *(
                    self.evaluate(list(x))
                    for x in itertools.product((False, True), repeat=self.input_size)
                )
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
    
    def _remove_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Remove gate from the ciurcuit without any checkings (!!!)

        :param: gate.
        :return: circuit without gate.

        """
        for operand in gate.operands:
            self._remove_user(operand, gate.label)

        self._elements.pop(gate.label, None)
        if gate.gate_type == INPUT:
            self._inputs.remove(gate.label)

        self._outputs = [x for x in self._outputs if x != gate]

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

    def _remove_user(self, element: Label, user: Label):
        """Adds user for `element`."""
        self._element_to_users[element].remove(user)

    def __str__(self):
        input_str = textwrap.shorten(
            'INPUTS: ' + '; '.join(f'{input_label}' for input_label in self._inputs),
            width=100,
        )
        output_str = textwrap.shorten(
            'OUTPUTS: '
            + '; '.join(f'{output_label}' for output_label in self._outputs),
            width=100,
        )
        return f"{self.__class__.__name__}\n\t{input_str}\n\t{output_str}"
