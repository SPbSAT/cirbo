"""Module contains implementation of Circuit class."""

import collections
import copy
import enum
import io
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
    GateDoesntExistError,
    GateNotInputError,
    GateStateError,
    TraverseMethodError,
)
from boolean_circuit_tool.core.circuit.gate import (
    ALWAYS_FALSE,
    ALWAYS_TRUE,
    Gate,
    GateType,
    INPUT,
    Label,
    NOT,
)
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.utils import (
    input_iterator_with_fixed_sum,
    order_list,
)
from boolean_circuit_tool.core.circuit.validation import (
    check_block_doesnt_exist,
    check_block_hasnt_users,
    check_gate_hasnt_users,
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
        circuit_owner: 'Circuit',
        inputs: list[Label],
        gates: list[Label],
        outputs: list[Label],
    ):
        self._name = name
        self._circuit_owner = circuit_owner
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
    def circuit_owner(self) -> 'Circuit':
        return self._circuit_owner

    def rename_gate(self, old_label: Label, new_label: Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace.
        :param new_label: gate's new label.
        :return: modified block.

        """
        for i, input_label in enumerate(self.inputs):
            if input_label == old_label:
                self.inputs[i] = new_label

        for i, gate_label in enumerate(self.gates):
            if gate_label == old_label:
                self.gates[i] = new_label

        for i, output_label in enumerate(self.outputs):
            if output_label == old_label:
                self.outputs[i] = new_label

        return self

    def delete_gate(self, gate_label: Label) -> tp_ext.Self:
        """
        Delete gate from block.

        :param gate_label: gate's label to delete.
        :return: modified block.

        """

        if gate_label in self.inputs:
            self._inputs = [input for input in self._inputs if input != gate_label]

        if gate_label in self.gates:
            self._gates = [gate for gate in self._gates if gate != gate_label]

        if gate_label in self.outputs:
            self._outputs = [output for output in self._outputs if output != gate_label]

        return self

    def into_circuit(self):
        new_Circuit = Circuit()

        for input in self.inputs:
            new_Circuit._emplace_gate(label=input, gate_type=INPUT)

        for gate_label in self.gates:
            gate = self.circuit_owner.get_gate(gate_label)
            new_Circuit._emplace_gate(
                label=gate.label,
                gate_type=gate.gate_type,
                operands=copy.copy(gate.operands),
            )

        new_Circuit.set_outputs(copy.copy(self.outputs))

        return new_Circuit


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
    def from_bench_file(file_path: str) -> "Circuit":
        """
        Initialization the circuit with given data from file.

        :param filepath: path to the file with the circuit

        """
        from boolean_circuit_tool.core.parser.bench import BenchToCircuit

        _parser = BenchToCircuit()

        path = pathlib.Path(file_path)
        with path.open() as file:
            return _parser.convert_to_circuit(file)

    @staticmethod
    def from_bench_string(string: str) -> "Circuit":
        """
        Initialization the circuit with given data from string.

        :param string: string to the data circuit

        """
        from boolean_circuit_tool.core.parser.bench import BenchToCircuit

        _parser = BenchToCircuit()

        with io.StringIO(string) as s:
            return _parser.convert_to_circuit(s)

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
        if idx >= len(self._inputs):
            raise GateDoesntExistError()
        return self._inputs[idx]

    def index_of_input(self, label: Label) -> int:
        """
        :param label: input label
        :return: inputs index which corresponds to the label

        """
        if label not in self._inputs:
            raise GateDoesntExistError()
        return self._inputs.index(label)

    def output_at_index(self, idx: int) -> Label:
        """
        :param idx: output index
        :return: outputs label which corresponds to the index

        """
        if idx >= len(self._outputs):
            raise GateDoesntExistError()
        return self._outputs[idx]

    def index_of_output(self, label: Label) -> int:
        """
        :param idx: output label
        :return: first outputs index which corresponds to the label

        """
        if label not in self._outputs:
            raise GateDoesntExistError()
        return self._outputs.index(label)

    def all_indexes_of_output(self, label: Label) -> list[int]:
        """
        :param idx: output label
        :return: all outputs indexes which corresponds to the label

        """
        if label not in self._outputs:
            raise GateDoesntExistError()
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

    def remove_gate(self, gate_label: Label) -> tp_ext.Self:
        """
        Remove gate from the circuit.

        :param gate: gate for deleting.
        :return: modified circuit.

        """
        gate = self.get_gate(gate_label)
        check_gates_exist((gate.label,), self)
        check_gate_hasnt_users(gate.label, self)
        return self._remove_gate(gate)

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

        gates: set[Label] = {output for output in outputs if output not in inputs}
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

        return self.make_block(name, list(gates), outputs, inputs)

    def make_block(
        self,
        name: Label,
        gates: list[Label],
        outputs: list[Label],
        inputs: tp.Optional[list[Label]] = None,
    ) -> Block:
        """
        Initializes a block with the provided data and adds it to the circuit.

        :param name: new block's name.
        :param gates: new block's gates.
        :param outputs: new block's outputs.
        :param inputs: new block's inputs. If the parameter is not specified, the
            algorithm will collect all the gates that affect the gates otside the block.
        :return: created block.

        """

        check_block_doesnt_exist(name, self)
        check_gates_exist(gates, self)
        check_gates_exist(outputs, self)
        if inputs is not None:
            check_gates_exist(inputs, self)
        else:
            gates_set: set[Label] = set(gates)
            inputs = []
            for gate in gates:
                for oper in self.get_gate(gate).operands:
                    if oper not in gates_set:
                        inputs.append(oper)

        new_block = Block(
            name=name,
            circuit_owner=self,
            inputs=inputs,
            gates=gates,
            outputs=outputs,
        )

        self._blocks[name] = new_block
        return new_block

    def delete_block(self, block_label: Label) -> tp_ext.Self:
        """
        Delete block from list of block in the circuit.

        :param block_label: block's label for deleting
        :return: modified circuit

        """
        del self._blocks[block_label]
        return self

    def remove_block(self, block_label: Label) -> tp_ext.Self:
        """
        Delete all gates from block from the circuit and block from list of block.

        :param block_label: block's label for deleting
        :return: modified circuit

        """
        block: Block = self.get_block(block_label)
        check_block_hasnt_users(block, self)

        for gate in block.gates:
            self._remove_gate(self.get_gate(gate))

        for block in self.blocks.values():
            if len(block.gates) == 0:
                self.delete_block(block.name)

        return self.delete_block(block_label)

    def connect_circuit(
        self,
        connect_to: list[Label],
        circuit: tp_ext.Self,
        connect_from: list[Label],
        *,
        circuit_name: Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where `connect_from` (gates of the new
        circuit) will be conecting to `connect_to` (gates of the base circuit). If
        `connect_from` is list of inputs, than connecting gates will has type and
        operands from base circuit, if its list of outputs, than connecting gates will
        has type and operands from the new circuit. Name of these gate takes always from
        base circuit. And all of the inputs and outputs of the new circuit which not be
        in connecting are added to the inputs and outputs of the base circuit,
        respectively.

        :param connect_to: list of gates from the base circuit that will be conecting with
            new circuit
        :param circuit: a new circuit that should expand the basic one
        :param connect_from: list of gates from the new circuit that will be conecting with
            the base one
        :param circuit_name: new block's name. If `circuit_name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == True, than the gates are added to the circuit
            without a prefix and doesnt matter `circuit_name` is an empty string or not. If
            add_prefix == False, the gates are added to the circuit wit a prefix only if
            `circuit_name` is not an empty string
        :return: modifed circuit

        """
        check_gates_exist(connect_to, self)
        check_block_doesnt_exist(circuit_name, self)
        check_gates_exist(connect_from, circuit)
        assert len(connect_to) == len(connect_from)

        prefix: str = ''
        if circuit_name != '' and add_prefix:
            prefix = circuit_name + '@'

        mapping: dict[Label, Label] = {}
        for i, old_name in enumerate(connect_from):
            mapping[old_name] = connect_to[i]

        old_to_new_names = copy.copy(mapping)
        gates_for_block: set[Label] = set()
        for gate in circuit.top_sort(inversed=True):
            if gate.label not in mapping:
                new_label: Label = prefix + gate.label
                old_to_new_names[gate.label] = new_label
                self.emplace_gate(
                    label=new_label,
                    gate_type=gate.gate_type,
                    operands=tuple(old_to_new_names[oper] for oper in gate.operands),
                )
                if gate.gate_type != INPUT:
                    gates_for_block.add(new_label)
            else:
                if connect_from[0] in circuit.outputs:  #
                    self._gates[old_to_new_names[gate.label]] = Gate(
                        label=old_to_new_names[gate.label],
                        gate_type=gate.gate_type,
                        operands=tuple(
                            old_to_new_names[oper] for oper in gate.operands
                        ),
                    )

        self._outputs = [
            output for output in self._outputs if output not in connect_to
        ] + [
            old_to_new_names[output]
            for output in circuit.outputs
            if output not in connect_from
        ]

        for block in circuit.blocks.values():
            new_block_name = prefix + block.name
            check_block_doesnt_exist(new_block_name, self)
            self._blocks[new_block_name] = Block(
                name=new_block_name,
                circuit_owner=self,
                inputs=[old_to_new_names[input] for input in block.inputs],
                gates=[old_to_new_names[input] for input in block.gates],
                outputs=[old_to_new_names[input] for input in block.outputs],
            )

        if circuit_name != '':
            new_block = Block(
                name=circuit_name,
                circuit_owner=self,
                inputs=[old_to_new_names[input] for input in circuit.inputs],
                gates=list(gates_for_block),
                outputs=[old_to_new_names[output] for output in circuit.outputs],
            )

            self._blocks[new_block.name] = new_block

        return self

    def extend_back_circuit(
        self,
        circuit: tp_ext.Self,
        *,
        circuit_name: Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where all of inputs of the new circuit
        will be all of the outputs of the base circuit.

        :param circuit: a new circuit that should expand the basic one
        :param circuit_name: new block's name. If `circuit_name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == True, than the gates are added to the circuit
            without a prefix and doesnt matter `circuit_name` is an empty string or not. If
            add_prefix == False, the gates are added to the circuit wit a prefix only if
            `circuit_name` is not an empty string
        :return: modifed circuit

        """
        return self.connect_circuit(
            self.outputs,
            circuit,
            connect_from=circuit.inputs,
            circuit_name=circuit_name,
            add_prefix=add_prefix,
        )

    def extend_front_circuit(
        self,
        circuit: tp_ext.Self,
        *,
        circuit_name: Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where all of outputs of the new circuit
        will be all of the inputs of the base circuit.

        :param circuit: a new circuit that should expand the basic one
        :param circuit_name: new block's name. If `circuit_name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == True, than the gates are added to the circuit
            without a prefix and doesnt matter `circuit_name` is an empty string or not. If
            add_prefix == False, the gates are added to the circuit wit a prefix only if
            `circuit_name` is not an empty string
        :return: modifed circuit

        """
        return self.connect_circuit(
            self.inputs,
            circuit,
            connect_from=circuit.outputs,
            circuit_name=circuit_name,
            add_prefix=add_prefix,
        )

    def add_circuit(
        self,
        circuit: tp_ext.Self,
        *,
        circuit_name: Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a new circuit to the base one, where the inputs and outputs of the new
        circuit are added to the inputs and outputs of the base circuit, respectively.

        :param circuit: a new circuit that should expand the basic one
        :param circuit_name: new block's name. If `circuit_name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == True, than the gates are added to the circuit
            without a prefix and doesnt matter `circuit_name` is an empty string or not. If
            add_prefix == False, the gates are added to the circuit wit a prefix only if
            `circuit_name` is not an empty string
        :return: modifed circuit

        """
        return self.connect_circuit(
            [],
            circuit,
            connect_from=[],
            circuit_name=circuit_name,
            add_prefix=add_prefix,
        )

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

        if old_label in self._outputs:
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

    def add_inputs(self, inputs: list[Label]) -> None:
        """Add new inputs in the circuit."""
        for input in inputs:
            check_label_doesnt_exist(input, self)
            self.emplace_gate(input, INPUT)

    def replace_inputs(
        self, inputs_to_true: list[Label], inputs_to_false: list[Label]
    ) -> tp_ext.Self:
        """
        Replaces inputs with gate ALWAYS_TRUE or ALWAYS_FASE, while removing them from
        the list of inputs of the circuit.

        :param inputs_to_true: inputs that need to be replaced with ALWAYS_TRUE.
        :param inputs_to_false: inputs that need to be replaced with ALWAYS_FALSE.
        :return: modified circuit.

        """

        def _replace_inputs(inputs: list[Label], new_type: GateType):
            for input_label in inputs:
                if self.get_gate(input_label).gate_type != INPUT:
                    raise GateNotInputError()
                self._gates[input_label] = Gate(input_label, new_type)
                self._inputs.remove(input_label)

        _replace_inputs(inputs_to_true, ALWAYS_TRUE)
        _replace_inputs(inputs_to_false, ALWAYS_FALSE)

        return self

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

    def evaluate(self, inputs: tp.Sequence[bool]) -> list[bool]:
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

    def evaluate_at(self, inputs: tp.Sequence[bool], output_index: int) -> bool:
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

    def _remove_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Remove gate from the circuit without any checkings (!!!).

        :param gate: gate for deleting.
        :return: modified circuit.

        """
        for operand in gate.operands:
            self._remove_user(operand, gate.label)

        del self._gates[gate.label]

        if gate.gate_type == INPUT:
            self._inputs.remove(gate.label)

        self._outputs = [output for output in self.outputs if output != gate.label]

        for block in self.blocks.values():
            block.delete_gate(gate.label)

        return self

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings (!!!)

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
        Add gate in the ciurcuit without any checkings (!!!).

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

    def _remove_user(self, gate: Label, user: Label):
        """Remove user from `gate`."""
        self._gate_to_users[gate].remove(user)

    def _add_user(self, gate: Label, user: Label):
        """Add user for `gate`."""
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

    def __copy__(self):
        new_circuit = Circuit()

        for gate in self.top_sort(inversed=True):
            new_circuit.emplace_gate(
                label=gate.label,
                gate_type=gate.gate_type,
                operands=copy.copy(gate.operands),
            )

        new_circuit.set_outputs(copy.copy(self.outputs))

        for block in self.blocks.values():
            new_circuit.make_block(
                name=block.name,
                gates=copy.copy(block.gates),
                outputs=copy.copy(block.outputs),
                inputs=copy.copy(block.inputs),
            )

        return new_circuit

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


if __name__ == '__main__':
    from boolean_circuit_tool.core.circuit.gate import AND, OR

    C0 = Circuit()
    C0.add_gate(Gate('x1', INPUT))
    C0.add_gate(Gate('x2', INPUT))
    C0.add_gate(Gate('x3', OR, ('x1', 'x2')))
    C0.mark_as_output('x3')

    C1 = Circuit()
    C1.add_gate(Gate('y1', INPUT))
    C1.add_gate(Gate('y2', NOT, ('y1',)))
    C1.add_gate(Gate('y3', AND, ('y1', 'y2')))
    C1.add_gate(Gate('y4', OR, ('y1', 'y2')))
    C1.mark_as_output('y3')
    C1.mark_as_output('y4')

    C2 = Circuit()
    C2.add_gate(Gate('A', INPUT))
    C2.add_gate(Gate('B', INPUT))
    C2.add_gate(Gate('C', AND, ('A', 'B')))
    C2.mark_as_output('C')

    C = Circuit()

    C.connect_circuit(
        connect_to=[],
        circuit=C0,
        connect_from=[],
        circuit_name='C_C0',
        add_prefix=False,
    )
    print('\n\n\n', C.format_circuit())

    C.connect_circuit(
        connect_to=C.inputs,
        circuit=C1,
        connect_from=C1.outputs,
        circuit_name='C1_C_C0',
        add_prefix=False,
    )
    print('\n\n\n', C.format_circuit())
