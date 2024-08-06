"""Module contains implementation of Circuit class."""

import collections
import copy
import enum
import itertools
import logging
import pathlib
import textwrap
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.boolean_function import BooleanFunction, RawTruthTable
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitGateAlreadyExistsError,
    CircuitGateIsAbsentError,
    CircuitIsCyclicalError,
    CreateBlockError,
    GateStateError,
    TraverseMethodError,
)
from boolean_circuit_tool.core.circuit.gate import Gate, GateType, INPUT, Label, NOT
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.utils import (
    input_iterator_with_fixed_sum,
    order_list,
)
from boolean_circuit_tool.core.circuit.validation import (
    check_block_doesnt_exist,
    check_gates_exist,
    check_label_doesnt_exist,
)

logger = logging.getLogger(__name__)

__all__ = ['Circuit', 'Block']


class TraverseMode(enum.Enum):
    DFS = 'DFS'
    BFS = 'BFS'


class TraverseState(enum.Enum):
    UNVISITED = 0
    ENTERED = 1
    VISITED = 2


TraverseHookT = tp.Callable[[Gate, tp.Mapping[Label, TraverseState]], None]


class Block:
    """
    Structure to carry block in circuit.

    Block consists as a list of Gates without relations between them and is represented
    a view for part of the circuit.

    """

    def __init__(
        self,
        name: Label,
        circuit: 'Circuit',
        inputs: list[Label],
        gates: list[Label],
        outputs: list[Label],
    ):
        self._name = name
        self._circuit_ref = circuit
        self._inputs = inputs
        self._gates = gates
        self._outputs = outputs

    @property
    def name(self) -> Label:
        return self._name

    @property
    def inputs(self) -> list[Label]:
        return self._inputs

    @property
    def gates(self) -> list[Label]:
        return self._gates

    @property
    def outputs(self) -> list[Label]:
        return self._outputs

    @property
    def circuit_ref(self) -> 'Circuit':
        return self._circuit_ref

    def rename_gate(self, old_label: Label, new_label: Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace.
        :param new_label: gate's new label.
        :return: modified block.

        """
        self._inputs = [
            new_label if input_label == old_label else input_label
            for input_label in self.inputs
        ]
        self._gates = [
            new_label if gate_label == old_label else gate_label
            for gate_label in self.gates
        ]
        self._outputs = [
            new_label if output_label == old_label else output_label
            for output_label in self.outputs
        ]
        return self

    def into_circuit(self):
        pass


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
        self._gates: dict[Label, Gate] = {}
        self._gate_to_users: tp.DefaultDict[Label, list[Label]] = (
            collections.defaultdict(list)
        )
        self._blocks: dict[Label, Block] = {}

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
    def gates(self) -> dict[Label, Gate]:
        """
        :return: dict of gates into the circuit.

        """
        return self._gates

    @property
    def blocks(self) -> dict[Label, Block]:
        """
        :return: dict of blocks into the circuit.

        """
        return self._blocks

    @property
    def size(self) -> int:
        """
        :return: number of gates into the circuit.

        """
        return len(self._gates)

    @property
    def gates_number(self, exclusion_list: list[GateType] = [INPUT, NOT]) -> int:
        """
        :return: number of gates that are not included in the exclusion list in the circuit.

        """
        return sum(
            1 for gate in self._gates.values() if gate.gate_type not in exclusion_list
        )

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

    def get_gate(self, label: Label) -> Gate:
        """
        :return: a specific gate from the circuit by `label`.

        """
        return self._gates[label]

    def get_gate_users(self, label: Label) -> list[Label]:
        """
        :return: list of gates which use given gate as operand.

        """
        return self._gate_to_users[label]

    def get_block(self, block_label: Label) -> Block:
        """
        :return: block from the circuit by label.

        """
        return self._blocks[block_label]

    def has_gate(self, label: Label) -> bool:
        """
        :return: True iff this circuit has gate `label`.

        """
        return label in self._gates

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param gate: new gate.
        :return: modified circuit.

        """
        check_label_doesnt_exist(gate.label, self)
        check_gates_exist(gate.operands, self)

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
        check_gates_exist(operands, self)

        return self._emplace_gate(label, gate_type, operands, **kwargs)

    def make_block_from_slice(
        self,
        name: Label,
        inputs: list[Label],
        outputs: list[Label],
    ) -> Block:
        """
        Initializes the block with the provided or collected data and adds it to the
        circuit. All the necessary for initializing the block are provided, except for
        the gates, they are collected by traversing the circuit from the given outputs
        to the given inputs. If the traversal has reached the input of the circuit, but
        this input is not present in the given list of inputs, the algorithm returns an
        error.

        :param name: new block's name
        :param inputs: new block's inputs
        :param outputs: new block's outputs
        :return: created block

        """
        check_block_doesnt_exist(name, self)
        check_gates_exist(inputs, self)
        check_gates_exist(outputs, self)

        gates: set[Label] = set(output for output in outputs if output not in inputs)
        queue: list[Label] = list(gates)
        while queue:

            cur_gate = queue.pop()
            for oper in self.get_gate(cur_gate).operands:
                if oper not in inputs:
                    if self.get_gate(oper).gate_type == INPUT:
                        raise CreateBlockError(
                            'The allocated block depends on a gate'
                            + 'that is not present in the inputs'
                        )
                    if oper not in gates:
                        gates.add(oper)
                        queue.append(oper)

        return self.make_block(name, inputs, list(gates), outputs)

    def make_block(
        self,
        name: Label,
        inputs: list[Label],
        gates: list[Label],
        outputs: list[Label],
    ) -> Block:
        """
        Initializes a block with the provided data and adds it to the circuit.

        :param name: new block's name
        :param inputs: new block's inputs
        :param gates: new block's gates
        :param outputs: new block's outputs
        :return: created block

        """

        check_block_doesnt_exist(name, self)
        check_gates_exist(inputs, self)
        check_gates_exist(gates, self)
        check_gates_exist(outputs, self)

        new_block = Block(
            name=name,
            circuit=self,
            inputs=inputs,
            gates=gates,
            outputs=outputs,
        )

        self._blocks[name] = new_block
        return new_block

    def connect_circuit(
        self,
        connect_to: list[Label],
        circuit: tp_ext.Self,
        *,
        circuit_name: Label = '',
    ) -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where `connect_to` will be the inputs
        of the new one and if the len of list is less than the number of inputs in the
        new circuit, then new corresponding inputs will be added to the base circuit.
        The list of circuit outputs is replenished with the outputs of the new circuit,
        and also the outputs that were used as inputs are removed from list of outputs.

        :param connect_to: list of gates that will be inputs to the newly added circuit
        :param circuit: a new circuit that should expand the basic one
        :param name: new block's name. iff name is blank string. If the name is an empty
            string, then no new block is created, and the gates are added to the circuit
            without a prefix
        :return: modifed circuit

        """
        check_gates_exist(connect_to, self)
        check_block_doesnt_exist(circuit_name, self)

        if circuit_name != '':
            circuit_name += '@'

        old_to_new_names: dict[Label, Label] = {}
        for i, old_name in enumerate(circuit.inputs):
            if i < len(connect_to):
                old_to_new_names[old_name] = connect_to[i]
            else:
                old_to_new_names[old_name] = circuit_name + old_name
                self.add_gate(Gate(old_to_new_names[old_name], INPUT))

        gates_for_block: set[Label] = set()
        for gate in circuit.top_sort(inversed=True):
            if gate.gate_type != INPUT:
                new_label: Label = circuit_name + gate.label
                gates_for_block.add(new_label)
                old_to_new_names[gate.label] = new_label
                self.emplace_gate(
                    label=new_label,
                    gate_type=gate.gate_type,
                    operands=tuple(old_to_new_names[oper] for oper in gate.operands),
                )

        self._outputs = [
            output for output in self._outputs if output not in connect_to
        ] + [old_to_new_names[output] for output in circuit.outputs]

        if circuit_name != '':
            new_block = Block(
                name=circuit_name[:-1],
                circuit=self,
                inputs=[old_to_new_names[input] for input in circuit.inputs],
                gates=list(gates_for_block),
                outputs=[old_to_new_names[output] for output in circuit.outputs],
            )

            self._blocks[new_block.name] = new_block

            for block in circuit.blocks.values():
                new_block_name = circuit_name + block.name
                check_block_doesnt_exist(new_block_name, self)
                self._blocks[new_block_name] = Block(
                    name=new_block_name,
                    circuit=self,
                    inputs=[old_to_new_names[input] for input in block.inputs],
                    gates=[old_to_new_names[input] for input in block.gates],
                    outputs=[old_to_new_names[input] for input in block.outputs],
                )

        return self

    def extend_circuit(self, circuit: tp_ext.Self, *, name: Label = '') -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where the inputs and outputs of the new
        circuit are added to the inputs and outputs of the base circuit, respectively.

        :param circuit: a new circuit that should expand the basic one
        :param name: new block's name. iff name is blank string. If the name is an empty
            string, then no new block is created, and the gates are added to the circuit
            without a prefix
        :return: modifed circuit

        """
        return self.connect_circuit(self.outputs, circuit, circuit_name=name)

    def add_circuit(self, circuit: tp_ext.Self, *, name: Label = '') -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where the outputs of the base one will
        be the inputs of the new one. The list of circuit outputs is replenished with
        the outputs of the new circuit, and also the outputs that were used as inputs
        are removed from list of outputs.

        :param circuit: a new circuit that should expand the basic one
        :param name: new block's name. iff name is blank string. If the name is an empty
            string, then no new block is created, and the gates are added to the circuit
            without a prefix
        :return: modifed circuit

        """
        return self.connect_circuit([], circuit, circuit_name=name)

    def rename_gate(self, old_label: Label, new_label: Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace.
        :param new_label: gate's new label.
        :return: modified circuit.

        """
        if old_label not in self._gates:
            raise CircuitGateIsAbsentError()

        if new_label in self._gates:
            raise CircuitGateAlreadyExistsError()

        if old_label in self._inputs:
            self._inputs[self.index_of_input(old_label)] = new_label

        for idx in self.all_indexes_of_output(old_label):
            self._outputs[idx] = new_label

        self._gates[new_label] = Gate(
            new_label,
            self._gates[old_label].gate_type,
            self._gates[old_label].operands,
        )

        self._gate_to_users[new_label] = self._gate_to_users[old_label]

        for user_label in self._gate_to_users[old_label]:
            self._gates[user_label] = Gate(
                user_label,
                self._gates[user_label].gate_type,
                tuple(
                    new_label if oper == old_label else oper
                    for oper in self._gates[user_label].operands
                ),
            )

        for operand_label in self._gates[old_label].operands:
            operand_users = self._gate_to_users[operand_label]
            assert old_label in operand_users
            operand_users[operand_users.index(old_label)] = new_label

        del self._gates[old_label]

        for block in self.blocks.values():
            block.rename_gate(old_label, new_label)

        return self

    def mark_as_output(self, label: Label) -> None:
        """Mark as output a gate and append it to the end of `self._outputs`."""
        check_gates_exist((label,), self)
        self._outputs.append(label)

    def set_outputs(self, outputs: list[Label]) -> None:
        """Set new outputs in the circuit."""
        check_gates_exist(outputs, self)
        self._outputs = outputs

    def order_inputs(self, inputs: list[Label]) -> tp_ext.Self:
        """
        Order input gates.

        Create a new list by copying `inputs` and then appending to it the
        gates of `self._inputs` that are not already in the resulting list.
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
        gates of `self._outputs` that are not already in the resulting list.
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

        if self.gates_number == 0:
            return

        _predecessors_getter = (
            (lambda elem: len(elem.operands))
            if inversed
            else (lambda elem: len(self.get_gate_users(elem.label)))
        )

        _successors_getter = (
            (lambda elem: self.get_gate_users(elem.label))
            if inversed
            else (lambda elem: elem.operands)
        )

        indegree_map: dict[Label, int] = {
            elem.label: _predecessors_getter(elem) for elem in self._gates.values()
        }

        queue: list[Label] = [
            label for label, value in indegree_map.items() if value == 0
        ]

        if not queue:
            raise CircuitIsCyclicalError()

        while queue:
            current_elem = self.get_gate(queue.pop())
            for succ in _successors_getter(current_elem):
                indegree_map[succ] -= 1
                if indegree_map[succ] == 0:
                    queue.append(succ)
            yield current_elem

    def dfs(
        self,
        start_gates: tp.Optional[list[Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        on_exit_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
    ) -> tp.Iterable[Gate]:
        """
        Performs a depth-first traversal the circuit (DFS) from a list of given starting
        nodes or, if start_gates is not given, from inputs if inversed=True, and outputs
        if inversed=False.

        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inversed == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param on_exit_hook: callable function which applies after visiting the gate
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :return: Iterator of gates, which traverse the circuit in bfs order.

        """
        return self._traverse_circuit(
            TraverseMode.DFS,
            start_gates,
            inverse=inverse,
            on_enter_hook=on_enter_hook,
            on_exit_hook=on_exit_hook,
            unvisited_hook=unvisited_hook,
        )

    def bfs(
        self,
        start_gates: tp.Optional[list[Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
    ) -> tp.Iterable[Gate]:
        """
        Performs a breadth-first traversal the circuit (BFS) from a list of given
        starting nodes or, if start_gates is not given, from inputs if inversed=True,
        and outputs if inversed=False.

        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inversed == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :return: Iterator of gates, which traverse the circuit in dfs order.

        """
        return self._traverse_circuit(
            TraverseMode.BFS,
            start_gates,
            inverse=inverse,
            on_enter_hook=on_enter_hook,
            unvisited_hook=unvisited_hook,
        )

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

        `assignment` can be on any gate of the circuit.

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
            cur_gate = self.get_gate(queue_[-1])

            for operand in cur_gate.operands:
                if operand not in assigment_dict:
                    queue_.append(operand)

            if cur_gate.label == queue_[-1]:
                assigment_dict[cur_gate.label] = cur_gate.operator(
                    *(assigment_dict[op] for op in cur_gate.operands)
                )
                queue_.pop()

        for gate in self.gates:
            assigment_dict.setdefault(gate, Undefined)

        return assigment_dict

    def evaluate_circuit_outputs(
        self,
        assigment: dict[str, GateState],
    ) -> dict[str, GateState]:
        """
        Evaluate the circuit with the given input values and return outputs assigment.

        :param assigment: full or partial assigment for inputs.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any gate of the circuit.

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
        answer = self.evaluate_circuit_outputs(dict_inputs)
        return tp.cast(list[bool], [answer[output] for output in self._outputs])

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
            for gate in self._gates.values()
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

        self._gates[gate.label] = gate
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

        self._gates[label] = Gate(label, gate_type, operands, **kwargs)
        if gate_type == INPUT:
            self._inputs.append(label)

        return self

    def _add_user(self, gate: Label, user: Label):
        """Adds user for `gate`."""
        self._gate_to_users[gate].append(user)

    def _traverse_circuit(
        self,
        mode: TraverseMode,
        start_gates: tp.Optional[list[Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        on_exit_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
    ) -> tp.Iterable[Gate]:
        """
        Performs a traversal the circuit from a list of given starting nodes or, if
        start_gates is not given, from inputs if inversed=True, and outputs if
        inversed=False.

        :param mode: type of the traversal the circuit (dfs/bfs).
        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inversed == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param on_exit_hook: callable function which applies after visiting all children
            of the gate
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :return: Iterator of gates, which traverse the circuit in dfs/bfs order.

        """

        if self.size == 0:
            return

        if mode == TraverseMode.BFS:
            pop_index: int = 0
        elif mode == TraverseMode.DFS:
            pop_index = -1
        else:
            raise TraverseMethodError()

        _next_getter = (
            (lambda elem: self.get_gate_users(elem.label))
            if inverse
            else (lambda elem: elem.operands)
        )

        if start_gates is not None:
            queue: list[Label] = copy.copy(start_gates)
        elif inverse:
            queue = copy.copy(self.inputs)
        else:
            queue = copy.copy(self.outputs)

        gate_states: dict[Label, TraverseState] = collections.defaultdict(
            lambda: TraverseState.UNVISITED
        )

        if mode == TraverseMode.BFS:

            def _bfs_remove(label):
                nonlocal pop_index, queue
                gate_states[label] = TraverseState.VISITED
                queue.pop(pop_index)
                return

        else:

            def _bfs_remove(_):
                return

        while queue:

            current_elem = self.get_gate(queue[pop_index])

            if gate_states[current_elem.label] == TraverseState.UNVISITED:
                on_enter_hook(current_elem, gate_states)
                gate_states[current_elem.label] = TraverseState.ENTERED

                for child in _next_getter(current_elem):
                    if gate_states[child] == TraverseState.UNVISITED:
                        queue.append(child)

                # in case of bfs we don't need to process the gate after passing
                # all its children, so we can immediately remove it from the queue
                _bfs_remove(current_elem.label)

                yield current_elem

            elif gate_states[current_elem.label] == TraverseState.ENTERED:
                on_exit_hook(current_elem, gate_states)
                gate_states[current_elem.label] = TraverseState.VISITED
                queue.pop(pop_index)

            elif gate_states[current_elem.label] == TraverseState.VISITED:
                queue.pop(pop_index)

            else:
                raise GateStateError()

        for label in self._gates:
            if gate_states[label] == TraverseState.UNVISITED:
                unvisited_hook(self.get_gate(label), gate_states)

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
