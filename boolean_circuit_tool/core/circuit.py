"""Implementation circuit's class."""

import collections
import logging
import os
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.gate import Gate, GateLabel, GateType
from boolean_circuit_tool.core.utils.validation import check_init_gates, check_not_exist_gates_label


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

    """

    @staticmethod
    def from_bench(stream: tp.Iterable) -> "Circuit":
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
        self.gates: dict[GateLabel:Gate] = {}

    # TODO def save_to_file

    # TODO def draw

    # TODO def top_sort

    def add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit.

        :param: gate
        :return: circuit with new gate

        """
        check_not_exist_gates_label(gate.label, self)
        if gate.gate_type == GateType.INPUT:
            self.input_gates.add(gate.label)
        else:
            check_init_gates(gate.operands, self)
            self.gates[gate.label] = gate

        return self

    def emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tp.Optional[tp.Tuple[GateLabel]] = None,
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit.

        :mandatory param label: new gate's label :mandatory param gate_type: new gate's
        type of operator :mandatory param operands: new gate's operands :optional params
        **kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        check_not_exist_gates_label(label, self)
        if gate_type == GateType.INPUT:
            self.input_gates.add(label)
        else:
            check_init_gates(operands, self)
            self.gates[label] = Gate(label, gate_type, operands, **kwargs)

        return self

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without checking the initialization of operands.

        :param: gate
        :return: circuit with new gate

        """
        if gate.gate_type == GateType.INPUT:
            self.input_gates.add(gate.label)
        else:
            self.gates[gate.label] = gate

        return self

    def _emplace_gate(
        self,
        label: GateLabel,
        gate_type: GateType,
        operands: tp.Optional[tp.Tuple[GateLabel]] = None,
        **kwargs,
    ) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without checking the initialization of operands.

        :mandatory param label: new gate's label :mandatory param gate_type: new gate's
        type of operator :mandatory param operands: new gate's operands :optional params
        **kwargs: others parameters for conctructing new gate
        :return: circuit with new gate

        """
        if gate_type == GateType.INPUT:
            self.input_gates.add(label)
        else:
            self.gates[label] = Gate(label, gate_type, operands, **kwargs)

        return self

    def rename_gate(self, old_label: GateLabel, new_label: GateLabel) -> tp_ext.Self:
        """
        Rename gate.

        :param old_label: gate's label to replace
        :param new_label: gate's new label
        :return: modified circuit

        """
        new_inputs = set()
        for input in self.input_gates:
            if input == old_label:
                new_inputs.add(new_label)
            else:
                new_inputs.add(input)
        self.input_gates = new_inputs

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


        new_outputs = set()
        for output in self.output_gates:
            if output == old_label:
                new_outputs.add(new_label)
            else:
                new_outputs.add(output)
        self.output_gates = new_outputs
        
        return self

    def mark_as_output(self, label: GateLabel) -> None:
        check_init_gates((label,), self)
        self.output_gates.add(label)

    def evaluate_circuit(self, assigment: tp.List[bool]) -> bool:
        """
        Evaluate the circuit with the given input values.

        :param assigment: assigment for inputs

        """
        assert len(assigment) == len(self.input_gates)

        assigment_dict = collections.defaultdict(-1)
        for i, input in enumerate(self.input_gates):
            assigment_dict[input] = assigment[i]

        for gate in self.gates:
            pass

        return 0

    @property
    def gates_number(self):
        """Return number of gates with inputs."""
        return len(self.gates) + len(self.input_gates)

    def __str__(self):
        s = ''

        for input_label in self.input_gates:
            s += f'INPUT({input_label})\n'
        s += '\n'

        for gate in self.gates:
            s += f'{gate}\n'
        s += '\n'

        for output_label in self.output_gates:
            s += f'OUTPUT({output_label})\n'

        return s
