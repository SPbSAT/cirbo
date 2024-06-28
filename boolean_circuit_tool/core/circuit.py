"""Implementation circuit's class."""

import collections
import logging
import typing as tp

import typing_extensions as tp_ext

from boolean_circuit_tool.core.gate import Gate, GateAssign, GateLabel, GateType
from boolean_circuit_tool.core.operators import (
    and_,
    iff_,
    mux_,
    nand_,
    nor_,
    not_,
    nxor_,
    or_,
    xor_,
)
from boolean_circuit_tool.core.utils.validation import (
    check_init_gates,
    check_not_exist_gates_label,
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
    TODO def save_to_file
    TODO def draw
    TODO def top_sort

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
        self.gates: dict[GateLabel, Gate] = {}

        self._operators: tp.Dict[GateType, tp.Callable] = {
            GateType.NOT: not_,
            GateType.AND: and_,
            GateType.NAND: nand_,
            GateType.OR: or_,
            GateType.NOR: nor_,
            GateType.XOR: xor_,
            GateType.NXOR: nxor_,
            GateType.IFF: iff_,
            GateType.BUFF: iff_,
            GateType.MUX: mux_,
        }

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
            check_init_gates(tuple(gate.operands), self)
            self.gates[gate.label] = gate

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
        check_not_exist_gates_label(label, self)
        if gate_type == GateType.INPUT:
            self.input_gates.add(label)
        else:
            check_init_gates(operands, self)
            self.gates[label] = Gate(label, gate_type, operands, **kwargs)

        return self

    def _add_gate(self, gate: Gate) -> tp_ext.Self:
        """
        Add gate in the ciurcuit without any checkings.

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
        check_init_gates((label,), self)
        self.output_gates.add(label)

    def evaluate_circuit(
        self,
        assigment: tp.List[bool],
    ) -> bool:  # или мы хотим вектор значений выходов схемы
        """
        Evaluate the circuit with the given input values.

        :param assigment: assigment for inputs

        """
        assert len(assigment) == len(self.input_gates)

        assigment_dict: dict = collections.defaultdict(lambda: GateAssign.UNDEFINED.value)
        for i, input in enumerate(sorted(self.input_gates)):
            assigment_dict[input] = assigment[i]

        queue_ = list()

        for output in self.output_gates:
            queue_.append(self.gates[output])

        for gate in queue_:
            for operand in gate.operands:
                if operand not in self.input_gates:
                    queue_.append(self.gates[operand])

        for gate in reversed(queue_):
            for operand in gate.operands:
                assert (
                    operand in assigment_dict
                    and assigment_dict[operand] != GateAssign.UNDEFINED.value
                )
            if gate.label not in assigment_dict:
                assigment_dict[gate.label] = self._operators[gate.gate_type](
                    *[assigment_dict[op] for op in gate.operands]
                )

        return all([assigment_dict[output] for output in self.output_gates])

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
