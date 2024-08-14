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

import graphviz
import typing_extensions as tp_ext

from boolean_circuit_tool.core.boolean_function import Function, RawTruthTable
from boolean_circuit_tool.core.circuit import gate
from boolean_circuit_tool.core.circuit.converters import convert_gate
from boolean_circuit_tool.core.circuit.exceptions import (
    CircuitGateAlreadyExistsError,
    CircuitGateIsAbsentError,
    CircuitIsCyclicalError,
    CircuitValidationError,
    CreateBlockError,
    GateDoesntExistError,
    GateNotInputError,
    GateStateError,
    OverlappingBlocksError,
    TraverseMethodError,
)
from boolean_circuit_tool.core.circuit.operators import GateState, Undefined
from boolean_circuit_tool.core.circuit.utils import (
    input_iterator_with_fixed_sum,
    order_list,
)
from boolean_circuit_tool.core.circuit.validation import (
    check_block_doesnt_exist,
    check_block_has_not_users,
    check_gate_has_not_users,
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


TraverseHookT = tp.Callable[[gate.Gate, tp.Mapping[gate.Label, TraverseState]], None]
TraverseStateHookT = tp.Callable[[tp.Mapping[gate.Label, TraverseState]], None]


class Block:
    """
    Structure to carry block in circuit.

    Block consists as a list of Gates without relations between them and represents a
    view for part of the circuit.

    """

    def __init__(
        self,
        name: gate.Label,
        owner: 'Circuit',
        inputs: list[gate.Label],
        gates: list[gate.Label],
        outputs: list[gate.Label],
    ):
        self._name = name
        self._owner = owner
        self._inputs = inputs
        self._gates = gates
        self._outputs = outputs

    @property
    def name(self) -> gate.Label:
        return self._name

    @property
    def inputs(self) -> list[gate.Label]:
        return self._inputs

    @property
    def gates(self) -> list[gate.Label]:
        return self._gates

    @property
    def outputs(self) -> list[gate.Label]:
        return self._outputs

    @property
    def circuit_owner(self) -> 'Circuit':
        return self._owner

    def _rename_gate(self, old_label: gate.Label, new_label: gate.Label) -> tp_ext.Self:
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

    def _delete_gate(self, label_for_deleting: gate.Label) -> tp_ext.Self:
        """
        Delete gate from block.

        :param label_for_deleting: gate's label to delete.
        :return: modified block.

        """

        if label_for_deleting in self.inputs:
            self._inputs = [
                _input for _input in self._inputs if _input != label_for_deleting
            ]

        if label_for_deleting in self.gates:
            self._gates = [
                gate_label
                for gate_label in self._gates
                if gate_label != label_for_deleting
            ]

        if label_for_deleting in self.outputs:
            self._outputs = [
                output for output in self._outputs if output != label_for_deleting
            ]

        return self

    def into_circuit(self):
        """
        Creates a new circuit by block's gates.

        The block inputs will also be added to the new circuit.

        """
        new_circuit = Circuit()

        for _input in self.inputs:
            new_circuit._emplace_gate(label=_input, gate_type=gate.INPUT)

        for gate_label in self.gates:
            cur_gate: gate.Gate = self._owner.get_gate(gate_label)
            new_circuit._emplace_gate(
                label=cur_gate.label,
                gate_type=cur_gate.gate_type,
                operands=copy.copy(cur_gate.operands),
            )

        new_circuit.set_outputs(self.outputs)

        for cur_gate in new_circuit.gates.values():
            check_gates_exist(cur_gate.operands, new_circuit)

        return new_circuit


class Circuit(Function):
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

        :param file_path: path to the file with the circuit

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

    @staticmethod
    def bare_circuit_with_labels(
        labels: tp.Sequence[gate.Label],
        *,
        set_as_outputs: bool = False,
    ) -> "Circuit":
        """
        Generates a circuit consisting of INPUT gates with labels from `labels`.

        :param labels: new input's labels.
        :param set_as_outputs: marked new inputs as OUTPUTS.
        :return: new Circuit

        """
        circuit = Circuit()
        circuit.add_inputs(labels)
        if set_as_outputs:
            circuit.set_outputs(labels)
        return circuit

    @staticmethod
    def bare_circuit(
        input_size: int,
        *,
        prefix: str = '',
        set_as_outputs: bool = False,
    ) -> "Circuit":
        """
        Generates a circuit consisting of input_size INPUT gates.

        :param input_size: number of input gates
        :param prefix: add prefix to input's labels
        :param set_as_outputs: marked new inputs as OUTPUTS.
        :return: new Circuit

        """
        return Circuit.bare_circuit_with_labels(
            labels=[f'{prefix}{i}' for i in range(input_size)],
            set_as_outputs=set_as_outputs,
        )

    def __init__(self):
        self._inputs: list[gate.Label] = list()
        self._outputs: list[gate.Label] = list()
        self._gates: dict[gate.Label, gate.Gate] = {}
        self._gate_to_users: tp.DefaultDict[gate.Label, list[gate.Label]] = (
            collections.defaultdict(list)
        )
        self._blocks: dict[gate.Label, Block] = {}

    @property
    def inputs(self) -> list[gate.Label]:
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
    def outputs(self) -> list[gate.Label]:
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
    def gates(self) -> dict[gate.Label, gate.Gate]:
        """
        :return: dict of gates into the circuit.

        """
        return self._gates

    @property
    def blocks(self) -> dict[gate.Label, Block]:
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

    def gates_number(
        self, exclusion_list: tp.Optional[tp.Container[gate.GateType]] = None
    ) -> int:
        """
        :return: number of gates that are not included in the exclusion list in the circuit.

        """
        if exclusion_list is None:
            exclusion_list = [
                gate.INPUT,
                gate.NOT,
                gate.LNOT,
                gate.RNOT,
                gate.IFF,
                gate.LIFF,
                gate.RIFF,
                gate.ALWAYS_FALSE,
                gate.ALWAYS_TRUE,
            ]
        return sum(
            1 for _gate in self._gates.values() if _gate.gate_type not in exclusion_list
        )

    def input_at_index(self, idx: int) -> gate.Label:
        """
        :param idx: input index
        :return: inputs label which corresponds to the index

        """
        if idx >= len(self._inputs):
            raise GateDoesntExistError()
        return self._inputs[idx]

    def index_of_input(self, label: gate.Label) -> int:
        """
        :param label: input label
        :return: inputs index which corresponds to the label

        """
        if label not in self._inputs:
            raise GateDoesntExistError()
        return self._inputs.index(label)

    def output_at_index(self, idx: int) -> gate.Label:
        """
        :param idx: output index
        :return: outputs label which corresponds to the index

        """
        if idx >= len(self._outputs):
            raise GateDoesntExistError()
        return self._outputs[idx]

    def index_of_output(self, label: gate.Label) -> int:
        """
        :param label: output label
        :return: first outputs index which corresponds to the label

        """
        if label not in self._outputs:
            raise GateDoesntExistError()
        return self._outputs.index(label)

    def all_indexes_of_output(self, label: gate.Label) -> list[int]:
        """
        :param label: output label
        :return: all outputs indexes which corresponds to the label

        """
        if label not in self._outputs:
            raise GateDoesntExistError()
        return [idx for idx, output in enumerate(self._outputs) if output == label]

    def get_gate(self, label: gate.Label) -> gate.Gate:
        """
        :return: a specific gate from the circuit by `label`.

        """
        return self._gates[label]

    def get_gate_users(self, label: gate.Label) -> list[gate.Label]:
        """
        :return: list of gates which use given gate as operand.

        """
        if label not in self._gates:
            raise GateDoesntExistError()
        return self._gate_to_users[label]

    def get_block(self, block_label: gate.Label) -> Block:
        """
        :return: block from the circuit by label.

        """
        return self._blocks[block_label]

    def has_gate(self, label: gate.Label) -> bool:
        """
        :return: True iff this circuit has gate `label`.

        """
        return label in self._gates

    def remove_gate(self, gate_label: gate.Label) -> tp_ext.Self:
        """
        Remove gate from the circuit.

        :param gate_label: gate for deleting.
        :return: this circuit after modification.

        """
        check_gates_exist((gate_label,), self)
        check_gate_has_not_users(gate_label, self)
        return self._remove_gate(gate_label)

    def add_gate(self, new_gate: gate.Gate) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param new_gate: new gate.
        :return: this circuit after modification.

        """
        check_label_doesnt_exist(new_gate.label, self)
        check_gates_exist(new_gate.operands, self)

        return self._add_gate(new_gate)

    def emplace_gate(
        self,
        label: gate.Label,
        gate_type: gate.GateType,
        operands: tuple[gate.Label, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the circuit.

        :param label: new gate's label.
        :param gate_type: new gate's type of operator.
        :param operands: new gate's operands.
        :param kwargs: others parameters for constructing new gate.
        :return: this circuit after modification.

        """
        check_label_doesnt_exist(label, self)
        check_gates_exist(operands, self)

        return self._emplace_gate(label, gate_type, operands, **kwargs)

    def get_internal_gates(
        self, inputs: list[gate.Label], outputs: list[gate.Label]
    ) -> list[gate.Label]:
        """
        Get gates between given inputs and outputs in the circuit.

        :param inputs: list with inputs.
        :param outputs: list with outputs.
        :return: list with gates from the circuit

        """
        internal_gates: list[gate.Label] = []
        label_is_visited: dict[gate.Label, bool] = collections.defaultdict(bool)
        for output_label in outputs:
            queue: tp.Deque[gate.Label] = collections.deque()
            if not label_is_visited[output_label]:
                label_is_visited[output_label]
                queue.append(output_label)
            while queue:
                label = queue.popleft()
                if label not in inputs and label not in outputs:
                    internal_gates.append(label)
                if label not in inputs:
                    for operand in self.get_gate(label).operands:
                        if not label_is_visited[operand]:
                            label_is_visited[operand] = True
                            queue.append(operand)
        return internal_gates

    def replace_subcircuit(
        self,
        subcircuit: "Circuit",
        inputs_mapping: dict[gate.Label, gate.Label],
        outputs_mapping: dict[gate.Label, gate.Label],
    ) -> tp_ext.Self:
        """
        Replace subcircuit with a new one.

        :param subcircuit: new subcircuit.
        :param inputs_mapping: label to label mapping between subcitcuit inputs and
            circuit nodes.
        :param outputs_mapping: label to label mapping between subcitcuit outputs and
            circuit nodes.
        :return: modified circuit.

        """
        labels_to_remove: list[gate.Label] = self.get_internal_gates(
            list(inputs_mapping.keys()), list(outputs_mapping.keys())
        )
        for label in outputs_mapping:
            if label in inputs_mapping:
                continue
            for operand in self.get_gate(label).operands:
                if operand in inputs_mapping or operand in outputs_mapping:
                    self._remove_user(operand, label)
        for label in labels_to_remove:
            self._remove_gate(label)

        tmp_mapping: dict[gate.Label, gate.Label] = (
            {}
        )  # used to avoid duplicating labels for nodes
        subcircuit_gates: list[gate.Label] = list(subcircuit.gates.keys())
        for i, label in enumerate(subcircuit_gates):
            new_label: gate.Label = (
                f"tmp_{i}"  # assume subcircuit will not have nodes with such labels
            )
            tmp_mapping[label] = new_label
            subcircuit.rename_gate(label, new_label)

        for label1, label2 in inputs_mapping.items():
            subcircuit.rename_gate(old_label=tmp_mapping[label2], new_label=label1)
        for label1, label2 in outputs_mapping.items():
            if label1 not in inputs_mapping:
                subcircuit.rename_gate(old_label=tmp_mapping[label2], new_label=label1)
        labels_to_rename: list[gate.Label] = list()
        for node in subcircuit.top_sort(inverse=True):
            label = node.label
            if label not in inputs_mapping and label not in outputs_mapping:
                self.add_gate(subcircuit.get_gate(label))
                labels_to_rename.append(label)
        for label in outputs_mapping:
            if label in inputs_mapping:
                continue
            self.get_gate(label)._operands = subcircuit.get_gate(label)._operands
            self.get_gate(label)._gate_type = subcircuit.get_gate(label)._gate_type
            for operand in self.get_gate(label)._operands:
                self._add_user(operand, label)
        for i, label in enumerate(labels_to_rename):
            new_label = labels_to_remove[i]
            self.rename_gate(label, new_label)

        return self

    def make_block_from_slice(
        self,
        name: gate.Label,
        inputs: tp.Sequence[gate.Label],
        outputs: tp.Sequence[gate.Label],
    ) -> Block:
        """
        Initializes the block with the provided or collected data and adds it to the
        circuit. All the necessary for initializing the block are provided, except for
        the gates, they are collected by traversing the circuit from the given outputs
        to the given inputs. If the traversal has reached the input of the circuit, but
        this input is not present in the given list of inputs, the algorithm raises.

        :param name: new block's name
        :param inputs: new block's inputs
        :param outputs: new block's outputs
        :return: created block

        """
        check_block_doesnt_exist(name, self)
        check_gates_exist(inputs, self)
        check_gates_exist(outputs, self)

        gates: set[gate.Label] = {output for output in outputs if output not in inputs}
        queue: list[gate.Label] = list(gates)
        while queue:

            cur_gate = queue.pop()
            for operand in self.get_gate(cur_gate).operands:
                if operand not in inputs:
                    if self.get_gate(operand).gate_type == gate.INPUT:
                        raise CreateBlockError(
                            'The allocated block depends on a gate '
                            'that is not present in the inputs'
                        )
                    if operand not in gates:
                        gates.add(operand)
                        queue.append(operand)

        return self.make_block(name, list(gates), outputs, inputs)

    def make_block(
        self,
        name: gate.Label,
        gates: tp.Sequence[gate.Label],
        outputs: tp.Sequence[gate.Label],
        inputs: tp.Optional[tp.Sequence[gate.Label]] = None,
    ) -> Block:
        """
        Initializes a block with the provided data and adds it to the circuit.

        :param name: new block's name.
        :param gates: new block's gates.
        :param outputs: new block's outputs.
        :param inputs: new block's inputs. If the parameter is not specified, the
            algorithm will collect all the gates that affect the gates outside the
            block.
        :return: created block.

        """

        check_block_doesnt_exist(name, self)
        check_gates_exist(gates, self)
        check_gates_exist(outputs, self)
        if inputs is not None:
            check_gates_exist(inputs, self)
        else:
            gates_set: set[gate.Label] = set(gates)
            inputs = []
            for _gate in gates:
                for operand in self.get_gate(_gate).operands:
                    if operand not in gates_set:
                        inputs.append(operand)

        new_block = Block(
            name=name,
            owner=self,
            inputs=list(inputs),
            gates=list(gates),
            outputs=list(outputs),
        )

        self._blocks[name] = new_block
        return new_block

    def delete_block(self, block_label: gate.Label) -> tp_ext.Self:
        """
        Delete block from list of block in the circuit.

        :param block_label: block's label for deleting
        :return: this circuit after modification

        """
        del self._blocks[block_label]
        return self

    def remove_block(self, block_label: gate.Label) -> tp_ext.Self:
        """
        Delete all gates from block from the circuit and block from list of block.

        :param block_label: block's label for deleting
        :return: this circuit after modification

        """
        block: Block = self.get_block(block_label)
        check_block_has_not_users(block, self)

        for _gate in block.gates:
            self._remove_gate(self.get_gate(_gate).label)

        self._blocks = {
            block_label: block
            for block_label, block in self.blocks.items()
            if len(block.gates) != 0
        }

        return self

    def connect_circuit(
        self,
        other: tp_ext.Self,
        this_connectors: tp.Sequence[gate.Label],
        other_connectors: tp.Sequence[gate.Label],
        *,
        right_connect: bool = False,
        name: gate.Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Connecting a new circuit (`other`) to the base one, where `other_connectors`
        (gates of the new circuit) will be connecting to `this_connectors` (gates of the
        base circuit). All inputs and outputs of the new circuit which not be in
        connecting are added to the inputs and outputs of the base circuit,
        respectively.

        :param other: a new circuit that should expand the basic one
        :param this_connectors: list of gates from the base circuit that will be connecting
            with new circuit
        :param other_connectors: list of gates from the new circuit that will be connecting
            with the base one
        :param right_connect:
            If `right_connect` == False, it means that `other_connectors` (from `circuit`)
            must be inputs, after connecting they will be replaced by `this_connectors`
            (from `self`).
            If `right_connect` == True, then `this_connectors` (from `self`) must be inputs,
            after connecting they will be replaced by `other_connectors` (from `circuit`).
        :param name: new block's name. If `name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == False, than the gates are added to the circuit
            without a prefix, and it doesn't matter if `name` is an empty string or
            not. If add_prefix == True, the gates are added to the circuit with a prefix only
            if `name` is not an empty string
        :return: this circuit after modification

        """
        check_block_doesnt_exist(name, self)
        check_gates_exist(this_connectors, self)
        check_gates_exist(other_connectors, other)
        if len(this_connectors) != len(other_connectors):
            raise CreateBlockError()
        if right_connect:
            for gate_label in this_connectors:
                if self.get_gate(gate_label).gate_type != gate.INPUT:
                    raise CreateBlockError()
        else:
            for gate_label in other_connectors:
                if other.get_gate(gate_label).gate_type != gate.INPUT:
                    raise CreateBlockError()

        copy_order_self_inputs = list(self._inputs)

        prefix: str = ''
        if name != '' and add_prefix:
            prefix = name + '@'

        mapping: dict[gate.Label, gate.Label] = {}
        for i, old_name in enumerate(other_connectors):
            mapping[old_name] = this_connectors[i]

        old_to_new_names = copy.copy(mapping)
        gates_for_block: set[gate.Label] = set()
        for _gate in other.top_sort(inverse=True):
            cur_gate: gate.Gate = _gate
            if cur_gate.label not in mapping:
                new_label: gate.Label = prefix + cur_gate.label
                old_to_new_names[cur_gate.label] = new_label
                self.emplace_gate(
                    label=new_label,
                    gate_type=cur_gate.gate_type,
                    operands=tuple(
                        old_to_new_names[operand] for operand in cur_gate.operands
                    ),
                )
                if cur_gate.gate_type != gate.INPUT:
                    gates_for_block.add(new_label)
            else:
                if right_connect:
                    self._gates[old_to_new_names[cur_gate.label]] = gate.Gate(
                        label=old_to_new_names[cur_gate.label],
                        gate_type=cur_gate.gate_type,
                        operands=tuple(
                            old_to_new_names[operand] for operand in cur_gate.operands
                        ),
                    )

        self.set_outputs(
            [output for output in self._outputs if output not in this_connectors]
            + [
                old_to_new_names[output]
                for output in other.outputs
                if output not in other_connectors
            ]
        )

        self.set_inputs(
            [
                _input
                for _input in copy_order_self_inputs
                if self._gates[_input].gate_type == gate.INPUT
            ]
            + [
                old_to_new_names[_input]
                for _input in other.inputs
                if _input not in other_connectors
            ]
        )

        for block in other.blocks.values():
            new_block_name = prefix + block.name
            check_block_doesnt_exist(new_block_name, self)
            self._blocks[new_block_name] = Block(
                name=new_block_name,
                owner=self,
                inputs=[old_to_new_names[_input] for _input in block.inputs],
                gates=[old_to_new_names[_gate] for _gate in block.gates],
                outputs=[old_to_new_names[_output] for _output in block.outputs],
            )

        if name != '':
            new_block = Block(
                name=name,
                owner=self,
                inputs=[old_to_new_names[_input] for _input in other.inputs],
                gates=list(gates_for_block),
                outputs=[old_to_new_names[_output] for _output in other.outputs],
            )

            self._blocks[new_block.name] = new_block

        return self

    def left_connect_circuit(
        self,
        other: tp_ext.Self,
        this_connectors: tp.Sequence[gate.Label],
        *,
        name: gate.Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Connecting a new circuit (`other`) to the base one, where inputs from `other`
        will be connecting to `this_connectors` (gates of the base circuit). All outputs
        of the new circuit which not be in connecting are added to the outputs of the
        base circuit.

        :param other: a new circuit that should expand the basic one
        :param this_connectors: list of gates from the base circuit that will be connecting
            with new circuit
        :param name: new block's name. If `name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == False, than the gates are added to the circuit
            without a prefix, and it doesn't matter if `name` is an empty string or
            not. If add_prefix == True, the gates are added to the circuit with a prefix only
            if `name` is not an empty string
        :return: this circuit after modification

        """

        return self.connect_circuit(
            other,
            this_connectors,
            other.inputs,
            right_connect=False,
            name=name,
            add_prefix=add_prefix,
        )

    def right_connect_circuit(
        self,
        other: tp_ext.Self,
        other_connectors: tp.Sequence[gate.Label],
        *,
        name: gate.Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Connecting a new circuit (`other`) to the base one, where `other_connectors`
        (gates of the new circuit) will be connecting to inputs from base circuit. All
        inputs and outputs of the new circuit which not be in connecting are added to
        the inputs and outputs of the base circuit, respectively.

        :param other: a new circuit that should expand the basic one
        :param other_connectors: list of gates from the new circuit that will be connecting
            with the base one
        :param name: new block's name. If `name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == False, than the gates are added to the circuit
            without a prefix, and it doesn't matter if `name` is an empty string or
            not. If add_prefix == True, the gates are added to the circuit with a prefix only
            if `name` is not an empty string
        :return: this circuit after modification

        """

        return self.connect_circuit(
            other,
            self.inputs,
            other_connectors,
            right_connect=True,
            name=name,
            add_prefix=add_prefix,
        )

    def extend_circuit(
        self,
        other: tp_ext.Self,
        *,
        this_connectors: tp.Optional[tp.Sequence[gate.Label]] = None,
        other_connectors: tp.Optional[tp.Sequence[gate.Label]] = None,
        right_connect: bool = False,
        name: gate.Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a circuit from the new one.

        :param other: a new circuit that should expand the basic one
        :param this_connectors: list of gates from the base circuit that will be connecting
            with new circuit
        :param other_connectors: list of gates from the new circuit that will be connecting
            with the base one
        :param right_connect: if right_connect == False, this means that the inputs
            of `circuit` will be replaced by the outputs of `self`, otherwise,
            then the outputs of `circuit` will become inputs for the `self`.
        :param circuit_name: new block's name. If `circuit_name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == False, than the gates are added to the circuit
            without a prefix, and it doesn't matter if `circuit_name` is an empty string or not.
            If add_prefix == True, the gates are added to the circuit with a prefix only if
            `circuit_name` is not an empty string
        :return: this circuit after modification

        """

        if this_connectors is None:
            this_connectors = self.inputs if right_connect else self.outputs
        if other_connectors is None:
            other_connectors = other.outputs if right_connect else other.inputs

        return self.connect_circuit(
            other,
            this_connectors,
            other_connectors,
            right_connect=right_connect,
            name=name,
            add_prefix=add_prefix,
        )

    def add_circuit(
        self,
        other: tp_ext.Self,
        *,
        name: gate.Label = '',
        add_prefix: bool = True,
    ) -> tp_ext.Self:
        """
        Extending a new circuit (`other`) to the base one, where the inputs and outputs
        of the new circuit are added to the inputs and outputs of the base circuit,
        respectively.

        :param other: a new circuit that should expand the basic one
        :param name: new block's name. If `name` is an empty string, then
            no new block is created, and the gates are added to the circuit without a prefix
        :param add_prefix: If add_prefix == False, than the gates are added to the circuit
            without a prefix, and it doesn't matter if `name` is an empty string or not.
            If add_prefix == True, the gates are added to the circuit with a prefix only if
            `name` is not an empty string
        :return: this circuit after modification

        """
        return self.connect_circuit(
            other=other,
            this_connectors=[],
            other_connectors=[],
            name=name,
            add_prefix=add_prefix,
        )

    def rename_gate(self, old_label: gate.Label, new_label: gate.Label) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace.
        :param new_label: gate's new label.
        :return: this circuit after modification.

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

        self._gates[new_label] = gate.Gate(
            new_label,
            self._gates[old_label].gate_type,
            self._gates[old_label].operands,
        )

        self._gate_to_users[new_label] = self._gate_to_users[old_label]

        for user_label in self._gate_to_users[old_label]:
            self._gates[user_label] = gate.Gate(
                user_label,
                self._gates[user_label].gate_type,
                tuple(
                    new_label if operand == old_label else operand
                    for operand in self._gates[user_label].operands
                ),
            )

        for operand_label in self._gates[old_label].operands:
            operand_users = self._gate_to_users[operand_label]
            assert old_label in operand_users
            operand_users[operand_users.index(old_label)] = new_label

        del self._gates[old_label]
        del self._gate_to_users[old_label]

        for block in self.blocks.values():
            block._rename_gate(old_label, new_label)

        return self

    def mark_as_output(self, label: gate.Label) -> None:
        """Mark as output a gate and append it to the end of `self._outputs`."""
        check_gates_exist((label,), self)
        self._outputs.append(label)

    def set_outputs(self, outputs: tp.Sequence[gate.Label]) -> None:
        """Set new outputs in the circuit."""
        check_gates_exist(outputs, self)
        self._outputs = list(outputs)

    def set_inputs(self, inputs: tp.Sequence[gate.Label]) -> None:
        """Set new order of inputs in the circuit."""
        check_gates_exist(inputs, self)
        for cur_gate in self.gates.values():
            if cur_gate.gate_type == gate.INPUT and cur_gate.label not in inputs:
                raise CircuitValidationError()

        new_inputs = list()
        for _input in inputs:
            if self.get_gate(_input).gate_type != gate.INPUT or _input in new_inputs:
                raise CircuitValidationError()
            new_inputs.append(_input)

        self._inputs = list(new_inputs)

    def add_inputs(self, inputs: tp.Sequence[gate.Label]) -> None:
        """Add new inputs in the circuit."""
        for _input in inputs:
            check_label_doesnt_exist(_input, self)
            self.emplace_gate(_input, gate.INPUT)

    def replace_inputs(
        self,
        inputs_to_true: tp.Sequence[gate.Label],
        inputs_to_false: tp.Sequence[gate.Label],
    ) -> tp_ext.Self:
        """
        Replaces inputs with gate ALWAYS_TRUE or ALWAYS_FALSE, while removing them from
        the list of inputs of the circuit.

        :param inputs_to_true: inputs that need to be replaced with ALWAYS_TRUE.
        :param inputs_to_false: inputs that need to be replaced with ALWAYS_FALSE.
        :return: this circuit after modification.

        """

        def _replace_inputs(inputs: tp.Sequence[gate.Label], new_type: gate.GateType):
            for input_label in inputs:
                if self.get_gate(input_label).gate_type != gate.INPUT:
                    raise GateNotInputError()
                self._gates[input_label] = gate.Gate(input_label, new_type)
                self._inputs.remove(input_label)

        _replace_inputs(inputs_to_true, gate.ALWAYS_TRUE)
        _replace_inputs(inputs_to_false, gate.ALWAYS_FALSE)

        return self

    def order_inputs(self, inputs: tp.Sequence[gate.Label]) -> tp_ext.Self:
        """
        Order input gates.

        Create a new list by copying `inputs` and then appending to it the
        gates of `self._inputs` that are not already in the resulting list.
        After that replaces `self._inputs` with this new list.

        :param inputs: full or partially ordered list of inputs.
        :return: this circuit after modification.

        """
        self._inputs = order_list(inputs, self._inputs)
        return self

    def order_outputs(self, outputs: tp.Sequence[gate.Label]) -> tp_ext.Self:
        """
        Order output gates.

        Create a new list by copying `outputs` and then appending to it the
        gates of `self._outputs` that are not already in the resulting list.
        After that replaces `self._outputs` with this new list.

        :param outputs: full or partially ordered list of outputs.
        :return: this circuit after modification.

        """
        self._outputs = order_list(outputs, self._outputs)
        return self

    def top_sort(self, *, inverse: bool = False) -> tp.Iterable[gate.Gate]:
        """
        :param inverse: a boolean value specifying the sort order.
            If inverse == True, Iterator will start from inputs, otherwise from outputs.
        :return: Iterator of gates, which sorted in topological order according Kana algorithm.

        """

        if self.size == 0:
            return

        _predecessors_getter = (
            (lambda elem: len(elem.operands))
            if inverse
            else (lambda elem: len(self.get_gate_users(elem.label)))
        )

        _successors_getter = (
            (lambda elem: self.get_gate_users(elem.label))
            if inverse
            else (lambda elem: elem.operands)
        )

        indegree_map: dict[gate.Label, int] = {
            elem.label: _predecessors_getter(elem) for elem in self._gates.values()
        }

        queue: list[gate.Label] = [
            label for label, value in indegree_map.items() if value == 0
        ]

        if not queue:
            raise CircuitIsCyclicalError()

        while queue:
            current_elem = self.get_gate(queue.pop())
            for successor in _successors_getter(current_elem):
                indegree_map[successor] -= 1
                if indegree_map[successor] == 0:
                    queue.append(successor)
            yield current_elem

    def dfs(
        self,
        start_gates: tp.Optional[tp.Sequence[gate.Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        on_discover_hook: TraverseHookT = lambda _, __: None,
        on_exit_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
        on_dfs_end_hook: TraverseStateHookT = lambda __: None,
    ) -> tp.Iterable[gate.Gate]:
        """
        Performs a depth-first traversal the circuit (DFS) from a list of given starting
        nodes or, if start_gates is not given, from inputs if inverse=True, and outputs
        if inverse=False.

        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inverse == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param on_discover_hook: callable function which applies for gate when we try to
            add it in queue
        :param on_exit_hook: callable function which applies after visiting the gate
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :param on_dfs_end_hook: callable that will be evaluated right before dfs ends.
        :return: Iterator of gates, which traverse the circuit in bfs order.

        """
        return self._traverse_circuit(
            TraverseMode.DFS,
            start_gates,
            inverse=inverse,
            on_enter_hook=on_enter_hook,
            on_discover_hook=on_discover_hook,
            on_exit_hook=on_exit_hook,
            unvisited_hook=unvisited_hook,
            on_dfs_end_hook=on_dfs_end_hook,
        )

    def bfs(
        self,
        start_gates: tp.Optional[tp.Sequence[gate.Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        on_discover_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
        on_dfs_end_hook: TraverseStateHookT = lambda __: None,
    ) -> tp.Iterable[gate.Gate]:
        """
        Performs a breadth-first traversal the circuit (BFS) from a list of given
        starting nodes or, if start_gates is not given, from inputs if inverse=True, and
        outputs if inverse=False.

        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inverse == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param on_discover_hook: callable function which applies for gate when we try to
            add it in queue
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :param on_dfs_end_hook: callable that will be evaluated right before dfs ends.
        :return: Iterator of gates, which traverse the circuit in dfs order.

        """
        return self._traverse_circuit(
            TraverseMode.BFS,
            start_gates,
            inverse=inverse,
            on_enter_hook=on_enter_hook,
            on_discover_hook=on_discover_hook,
            unvisited_hook=unvisited_hook,
            on_dfs_end_hook=on_dfs_end_hook,
        )

    def evaluate_full_circuit(
        self,
        assignment: dict[gate.Label, GateState],
    ) -> dict[gate.Label, GateState]:
        """
        Evaluate all gates of the circuit based on the provided assignment.

        :param assignment: full or partial assignment for inputs.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any gate of the circuit.

        """
        assignment_dict: dict[gate.Label, GateState] = dict(assignment)
        for _input in self._inputs:
            assignment_dict.setdefault(_input, Undefined)

        # Traverse this circuit in topological sorting from inputs to outputs.
        for cur_gate in self.top_sort(inverse=True):
            if cur_gate.gate_type == gate.INPUT:
                continue

            assignment_dict[cur_gate.label] = cur_gate.operator(
                *(assignment_dict[op] for op in cur_gate.operands)
            )

        return assignment_dict

    def evaluate_circuit(
        self,
        assignment: dict[gate.Label, GateState],
        *,
        outputs: tp.Optional[tp.Sequence[gate.Label]] = None,
    ) -> dict[gate.Label, GateState]:
        """
        Evaluate the circuit with the given partial assignment and return full
        assignment.

        Note: part unreachable from provided `outputs` will be `Undefined`.

        :param assignment: full or partial assignment for inputs.
        :param outputs: set of outputs which need to be evaluated. Those outputs will
               be used to initialise depth-first iteration across the circuit.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any gate of the circuit.

        """
        assignment_dict: dict[str, GateState] = dict(assignment)
        for _input in self._inputs:
            assignment_dict.setdefault(_input, Undefined)

        queue_: list[gate.Label] = list()

        _outputs = self._outputs if outputs is None else outputs
        for output in _outputs:
            if output not in self._inputs:
                queue_.append(output)

        while queue_:
            cur_gate = self.get_gate(queue_[-1])

            for operand in cur_gate.operands:
                if operand not in assignment_dict:
                    queue_.append(operand)

            if cur_gate.label == queue_[-1]:
                assignment_dict[cur_gate.label] = cur_gate.operator(
                    *(assignment_dict[op] for op in cur_gate.operands)
                )
                queue_.pop()

        for _gate in self.gates:
            assignment_dict.setdefault(_gate, Undefined)

        return assignment_dict

    def evaluate_circuit_outputs(
        self,
        assignment: dict[gate.Label, GateState],
    ) -> dict[gate.Label, GateState]:
        """
        Evaluate the circuit with the given input values and return outputs assignment.

        :param assignment: full or partial assignment for inputs.
        :return: outputs dictionary with the obtained values.

        `assignment` can be on any gate of the circuit.

        """
        assignment_dict: dict[gate.Label, GateState] = self.evaluate_circuit(assignment)

        return {output: assignment_dict[output] for output in self._outputs}

    def evaluate(self, inputs: tp.Sequence[bool]) -> list[bool]:
        """
        Get output values that correspond to provided `inputs`.

        :param inputs: values of input gates.
        :return: value of outputs evaluated for input values `inputs`.

        """
        dict_inputs: dict[str, GateState] = {}
        for i, _input in enumerate(self._inputs):
            dict_inputs[_input] = inputs[i]

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
        dict_inputs: dict[gate.Label, GateState] = {}
        for i, _input in enumerate(self._inputs):
            dict_inputs[_input] = inputs[i]

        label_output = self.output_at_index(output_index)
        # we can do cast because of the complete assignment we know
        # that Undefined will not appear
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

    def is_monotone(self, inverse: bool = False) -> bool:
        """
        Check if all outputs are monotone (output value doesn't decrease when
        inputs are enumerated in a classic order: 0000, 0001, 0010, 0011 ...).

        :param inverse: if True, will check that output values doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff this function is monotone.

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

    def is_monotone_at(self, output_index: int, inverse: bool = False) -> bool:
        """
        Check if output `output_index` is monotone (output value doesn't
        decrease when inputs are enumerated in a classic order: 0000, 0001,
        0010, 0011 ...).

        :param output_index: index of desired output.
        :param inverse: if True, will check that output value doesn't
        increase when inputs are enumerated in classic order.
        :return: True iff output `output_index` is monotone.

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
        output_index: tp.Sequence[int],
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

    def into_bench(self) -> tp_ext.Self:
        """
        Convert circuit into bench format.

        :return: this circuit after modification.

        """
        old_gates = copy.copy(self.gates)
        for cur_gate in old_gates.values():
            convert_gate(cur_gate, self)
        return self

    def into_graphviz_digraph(
        self,
        *,
        draw_blocks: bool = True,
        draw_labels: bool = False,
        name_graph: str = '',
        fontsize: str = '20',
        change_labels: bool = False,
        as_bench: bool = False,
    ) -> graphviz.Digraph:
        """
        Convert circuit to graphviz.Digraph.

        :param draw_blocks: if draw_blocks == True circuit's block are highlighted with
            a square, otherwise not.
        :param draw_labels: if draw_labels == True next to the operator type the name of
            the gate is written, if draw_labels == False circuit node names is type of
            operator.
        :param name_graph: name of graph.
        :param fontsize: fontsize for label of graph.
        :param change_labels: replace gates' labels with `x_{i}`, where `i` is the
            ordinal number of the gate in the circuit (`circuit.gates`)
        :param as_bench: draw the circuit in bench format
        :return: graph

        """
        _gate_type_to_name: dict[gate.GateType, str] = {
            gate.INPUT: "",
            gate.ALWAYS_TRUE: "1",
            gate.ALWAYS_FALSE: "0",
            gate.AND: u"\u2227",
            gate.GEQ: u"\u2265",
            gate.GT: u"\u003E",
            gate.IFF: "IFF",
            gate.LEQ: u"\u2264",
            gate.LIFF: "LIFF",
            gate.LNOT: u"\u00AC",
            gate.LT: u"\u003C",
            gate.NAND: u"\u00AC\u2227",
            gate.NOR: u"\u00AC\u2228",
            gate.NOT: u"\u00AC",
            gate.NXOR: u"\u00AC\u2295",
            gate.OR: u"\u2228",
            gate.RIFF: "RIFF",
            gate.RNOT: u"\u00AC",
            gate.XOR: u"\u2295",
        }

        circuit: Circuit = copy.copy(self)

        if as_bench:
            circuit.into_bench()

        if change_labels:
            labels = {
                _gate_label: f'x_{i}' for i, _gate_label in enumerate(circuit.gates)
            }
        else:
            labels = {_gate_label: _gate_label for _gate_label in circuit.gates}

        # Define node name formatting.
        if draw_labels:
            _create_node = lambda _gate_label, _gate: graph.node(
                _gate_label,
                label=f'{labels[_gate.label]}: {_gate_type_to_name[_gate.gate_type]}',
                shape='circle',
                fontsize='10',
            )
        else:
            _create_node = lambda _gate_label, _gate: graph.node(
                _gate_label,
                label=f'{_gate_type_to_name[_gate.gate_type]}',
                shape='circle',
                fixedsize='true',
                fontsize='10',
                height='0.25',
                width='0.25',
            )

        def _find_operand(operand: gate.Label) -> gate.Label:
            _gate = circuit.get_gate(operand)
            if _gate.gate_type in [gate.IFF, gate.LIFF]:
                return _find_operand(_gate.operands[0])
            elif _gate.gate_type == gate.RIFF:
                return _find_operand(_gate.operands[1])
            return _gate.label

        graph: graphviz.Digraph = graphviz.Digraph(name_graph)

        # Add all circuit nodes to graphviz digraph.
        for gate_label, cur_gate in circuit._gates.items():

            if cur_gate.gate_type in [gate.IFF, gate.LIFF, gate.RIFF]:
                continue

            _create_node(gate_label, cur_gate)

            if cur_gate.gate_type in [gate.GT, gate.GEQ, gate.LT, gate.LEQ]:
                for i, operand in enumerate(cur_gate.operands):
                    graph.edge(
                        _find_operand(operand),
                        gate_label,
                        headlabel=f'{i}',
                        labeldistance='2',
                        fontcolor='red',
                        fontsize='10',
                        arrowhead='vee',
                        penwidth='0.3',
                    )
            elif cur_gate.gate_type == gate.LNOT:
                graph.edge(
                    _find_operand(cur_gate.operands[0]),
                    gate_label,
                    arrowhead='vee',
                    penwidth='0.3',
                )
            elif cur_gate.gate_type == gate.RNOT:
                graph.edge(
                    _find_operand(cur_gate.operands[1]),
                    gate_label,
                    arrowhead='vee',
                    penwidth='0.3',
                )
            else:
                for operand in cur_gate.operands:
                    graph.edge(
                        _find_operand(operand),
                        gate_label,
                        arrowhead='vee',
                        penwidth='0.3',
                    )

        # Redraw inputs with different shape.
        for _input in circuit._inputs:
            graph.node(_input, label=labels[_input], shape='ellipse', color='white')

        # Redraw outputs with different shape.
        for _output in circuit._outputs:
            graph.node(_find_operand(_output), fillcolor="gray", style="rounded,filled")

        # Draw blocks as dot subgraphs if required.
        if draw_blocks and len(circuit._blocks.values()) > 0:

            nested_blocks: dict[gate.Label, list[gate.Label]] = collections.defaultdict(
                list
            )
            nested_blocks_rev: dict[gate.Label, list[gate.Label]] = (
                collections.defaultdict(list)
            )
            block_to_gates: dict[gate.Label, set[gate.Label]] = {}

            for _block in circuit._blocks.values():
                _block_gates = set(_block.gates)

                # Calculate blocks nestness
                for _other_block_label, _other_block_gates in block_to_gates.items():
                    intersection = _block_gates & _other_block_gates
                    if intersection:
                        if (
                            intersection != _block_gates
                            and intersection != _other_block_gates
                        ):
                            raise OverlappingBlocksError(
                                "Can't draw circuit with overlapping blocks. Either disable "
                                "'draw_blocks' option, or provide another circuit."
                            )
                        elif intersection == _block_gates:
                            nested_blocks[_other_block_label].append(_block.name)
                            nested_blocks_rev[_block.name].append(_other_block_label)
                        else:
                            nested_blocks[_block.name].append(_other_block_label)
                            nested_blocks_rev[_other_block_label].append(_block.name)

                block_to_gates[_block.name] = _block_gates

            # Function to draw nested subgraphs.
            def _draw_subgraph(_sg, _block_label):
                _sg.attr(color='blue')
                for _gate in circuit.get_block(_block_label).gates:
                    if circuit.get_gate(_gate).gate_type in [
                        gate.IFF,
                        gate.LIFF,
                        gate.RIFF,
                    ]:
                        continue
                    _sg.node(_gate)
                _sg.attr(label=_block_label, fontcolor='blue')
                for _subblock in nested_blocks[_block_label]:
                    with _sg.subgraph(name='cluster_' + _subblock) as _sbg:
                        _draw_subgraph(_sbg, _subblock)

            for block_label in circuit.blocks.keys():
                dependencies = nested_blocks_rev[block_label]
                if dependencies == []:
                    with graph.subgraph(name='cluster_' + block_label) as sg:
                        _draw_subgraph(sg, block_label)

        graph.attr(label=name_graph)
        graph.attr(fontsize=fontsize)

        return graph

    def render_graph(
        self,
        path: str,
        *,
        draw_blocks: bool = True,
        draw_labels: bool = False,
        name_graph: str = 'Circuit',
        fontsize: str = '20',
        change_labels: bool = False,
        as_bench: bool = False,
    ) -> None:
        """
        Save the circuit to the file like a drawing.

        :param path: path where you want to save the drawing.
        :param draw_blocks: if draw_blocks == True circuit's block are highlighted with
            a square, otherwise not.
        :param draw_labels: if draw_labels == True next to the operator type the name of
            the gate is written, if draw_labels == False circuit node names is type of
            operator.
        :param name_graph: name of graph.
        :param fontsize: fontsize for label of graph.
        :param change_labels: replace gates' labels with `x_{i}`, where `i` is the
            ordinal number of the gate in the circuit (`circuit.gates`).
        :param as_bench: draw the circuit in bench format.
        :param fontsize: fontsize for label of graph.

        """
        graph: graphviz.Digraph = self.into_graphviz_digraph(
            draw_blocks=draw_blocks,
            draw_labels=draw_labels,
            name_graph=name_graph,
            fontsize=fontsize,
            change_labels=change_labels,
            as_bench=as_bench,
        )
        graph.render(path)

    def save_to_file(self, path: str) -> None:
        """
        Save circuit to file.

        :param path: path to file with file's name and file's extension.

        """
        p = pathlib.Path(path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=False)
        p.write_text(self.format_circuit())

    def format_circuit(self) -> str:
        """Formats circuit as string in BENCH format."""

        input_str = '\n'.join(f'INPUT({input_label})' for input_label in self._inputs)
        gates_str = '\n'.join(
            _gate.format_gate()
            for _gate in self._gates.values()
            if _gate.gate_type != gate.INPUT
        )
        output_str = '\n'.join(
            f'OUTPUT({output_label})' for output_label in self._outputs
        )
        return f"{input_str}\n\n{gates_str}\n\n{output_str}"

    def _remove_gate(self, gate_label: gate.Label) -> tp_ext.Self:
        """
        Remove gate from the circuit without any checks (!!!).

        :param gate_label: gate's label for deleting.
        :return: this circuit after modification.

        """
        cur_gate = self.get_gate(gate_label)
        for operand in cur_gate.operands:
            self._remove_user(operand, gate_label)

        del self._gates[gate_label]

        if cur_gate.gate_type == gate.INPUT:
            self._inputs.remove(gate_label)

        if gate_label in self.outputs:
            self._outputs = [output for output in self.outputs if output != gate_label]

        for block in self.blocks.values():
            block._delete_gate(gate_label)

        return self

    def _add_gate(self, new_gate: gate.Gate) -> tp_ext.Self:
        """
        Add gate in the circuit without any checks (!!!)

        :param: new_gate.
        :return: circuit with new gate.

        """
        for operand in new_gate.operands:
            self._add_user(operand, new_gate.label)

        self._gates[new_gate.label] = new_gate
        if new_gate.gate_type == gate.INPUT:
            self._inputs.append(new_gate.label)

        return self

    def _emplace_gate(
        self,
        label: gate.Label,
        gate_type: gate.GateType,
        operands: tuple[gate.Label, ...] = (),
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the circuit without any checks (!!!).

        :param label: new gate's label.
        :param gate_type: new gate's type of operator.
        :param operands: new gate's operands.
        :params kwargs: others parameters for constructing new gate.
        :return: circuit with new gate.

        """
        for operand in operands:
            self._add_user(operand, label)

        self._gates[label] = gate.Gate(label, gate_type, operands, **kwargs)
        if gate_type == gate.INPUT:
            self._inputs.append(label)

        return self

    def _remove_user(self, gate_label: gate.Label, user: gate.Label):
        """Remove user from `gate`."""
        self._gate_to_users[gate_label].remove(user)

    def _add_user(self, gate_label: gate.Label, user: gate.Label):
        """Add user for `gate`."""
        self._gate_to_users[gate_label].append(user)

    def _traverse_circuit(
        self,
        mode: TraverseMode,
        start_gates: tp.Optional[tp.Sequence[gate.Label]] = None,
        *,
        inverse: bool = False,
        on_enter_hook: TraverseHookT = lambda _, __: None,
        on_discover_hook: TraverseHookT = lambda _, __: None,
        on_exit_hook: TraverseHookT = lambda _, __: None,
        unvisited_hook: TraverseHookT = lambda _, __: None,
        on_dfs_end_hook: TraverseStateHookT = lambda __: None,
    ) -> tp.Iterable[gate.Gate]:
        """
        Performs a traversal the circuit from a list of given starting nodes or, if
        start_gates is not given, from inputs if inverse=True, and outputs if
        inverse=False.

        :param mode: type of the traversal the circuit (dfs/bfs).
        :param start_gates: initial list of gates to traverse
        :param inverse: a boolean value specifying the sort order. If inverse == True,
            Iterator will start from inputs and traverse the circuit to the outputs,
            otherwise from outputs to inputs.
        :param on_enter_hook: callable function which applies before visiting the gate
        :param on_discover_hook: callable function which applies for gate when we try to
            add it in queue
        :param on_exit_hook: callable function which applies after visiting all children
            of the gate
        :param unvisited_hook: callable function which applies for unvisited gates after
            traverse circuit
        :param on_dfs_end_hook: callable that will be evaluated right before dfs ends.
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
            queue: list[gate.Label] = list(start_gates)
        elif inverse:
            queue = list(self.inputs)
        else:
            queue = list(self.outputs)

        gate_states: dict[gate.Label, TraverseState] = collections.defaultdict(
            lambda: TraverseState.UNVISITED
        )

        if mode == TraverseMode.BFS:

            def _bfs_remove(_label):
                nonlocal pop_index, queue
                gate_states[_label] = TraverseState.VISITED
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
                    on_discover_hook(self.get_gate(child), gate_states)
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

        on_dfs_end_hook(gate_states)

    def __eq__(self, other: tp.Any):
        """
        Compares two circuits.

        Two circuits different only by blocks considered equal.

        """
        if not isinstance(other, Circuit):
            return NotImplemented
        return (
            True
            and self.gates == other.gates
            and self.outputs == other.outputs
            and self.inputs == other.inputs
        )

    def __copy__(self):
        new_circuit = Circuit()

        for cur_gate in self.top_sort(inverse=True):
            new_circuit.emplace_gate(
                label=cur_gate.label,
                gate_type=cur_gate.gate_type,
                operands=copy.copy(cur_gate.operands),
            )

        new_circuit.set_inputs(self.inputs)
        new_circuit.set_outputs(self.outputs)

        for block in self.blocks.values():
            new_circuit.make_block(
                name=block.name,
                gates=block.gates,
                outputs=block.outputs,
                inputs=block.inputs,
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
