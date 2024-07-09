"""Implementation of .bench parsing."""

import abc
import logging
import typing as tp

from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import (
    AND,
    BUFF,
    GateType,
    IFF,
    INPUT,
    NAND,
    NOR,
    NOT,
    NXOR,
    OR,
    XOR,
)
from boolean_circuit_tool.core.circuit.validation import check_elements_exist
from boolean_circuit_tool.core.parser.abstract import AbstractParser


logger = logging.getLogger(__name__)

__all__ = ['AbstractBenchParser', 'BenchToCircuit']


class AbstractBenchParser(AbstractParser, metaclass=abc.ABCMeta):
    """
    Base abstract class for CircuitSAT.BENCH Parsers.

    Defines the way lines of BENCH file will be parsed. Also contains
    additional data, that will be collected while parsing.

    Input of AbstractBenchParser must be an Iterable[str],
    elements of which are BENCH instance lines.

    Any derived class must implement methods of Operator Gate processing.

    :attribute gate_to_integer_dict - carries mapping of gate
    names to their unique integer encoding.
    :attribute gate_number - number of last encoded gate. If
    equals to `0`, no gate was parsed yet.
    :attribute input_gates - set of encoded input gates;
    :attribute output_gates - set of encoded output gates;
    :property integer_to_gate_dict - inverted gate_to_integer_dict,
    maps integer encodings on gate names they encode.

    """

    def __init__(self, *args, **kwargs):
        super(AbstractBenchParser, self).__init__(*args, **kwargs)
        # Dict of specific processing methods for gates
        self._processings: dict[str, tp.Callable] = {
            NOT.name: self._process_not,
            AND.name: self._process_and,
            NAND.name: self._process_nand,
            OR.name: self._process_or,
            NOR.name: self._process_nor,
            XOR.name: self._process_xor,
            NXOR.name: self._process_nxor,
            IFF.name: self._process_iff,
            BUFF.name: self._process_iff,
        }

    def _process_line(self, line: str) -> tp.Iterable:
        logger.debug(f'Parsing line: "{line}"')
        if line == '' or line == '\n' or line[0] == '#':
            # Empty or comment line
            return []
        elif line.upper().startswith('INPUT'):
            # Input Gate
            return self._process_input_gate(line)
        elif line.upper().startswith('OUTPUT'):
            # Output Gate
            return self._process_output_gate(line)
        else:
            # Operator Gate
            return self._process_operator_gate(line)

    def _parse_operator_gate(self, line: str) -> tuple[str, str, list[str]]:
        """
        Parses line with operator gate.

        :returns (operator: str, result_gate: str, operands: List[str]).

        """

        _eq_idx = line.find('=')
        _lbkt_idx = line.find('(')
        _rbkt_idx = line.find(')')

        if _eq_idx == -1 or _lbkt_idx == -1 or _rbkt_idx == -1:
            raise ValueError(f"Can't parse {line}.")

        _operator_str = line[(_eq_idx + 1) : _lbkt_idx].strip(' ').upper()
        _out = line[:_eq_idx].strip(' ')
        _args_str = line[(_lbkt_idx + 1) : _rbkt_idx].strip(' ')
        logger.debug(
            f"\tLine read as: OPERATOR: `{_operator_str}`; "
            f"OPERATOR GATE: `{_out}`; OPERANDS: `{_args_str}`;"
        )

        _operands = [a.strip(' ') for a in _args_str.split(",")]
        logger.debug(
            f"\tParsed line as: OPERATOR: `{_operator_str}`; "
            f"OPERATOR GATE: `{_out}`; OPERANDS: `{_operands}`;"
        )

        return _operator_str, _out, _operands

    def _process_operator_gate(self, line: str) -> tp.Iterable:
        _operator, _out, _operands = self._parse_operator_gate(line)
        try:
            return self._processings[_operator](_out, *_operands)
        except KeyError:
            raise ValueError(f"Unknown operator {_operator}!")

    @abc.abstractmethod
    def _process_input_gate(self, line: str) -> list:
        """Parses line with input gate."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_output_gate(self, line: str) -> list:
        """Parses line with output gate."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_not(self, out: str, arg: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_and(self, out: str, arg1: str, arg2: str, *args: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_nand(self, out: str, arg1: str, arg2: str, *args: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_or(self, out: str, arg1: str, arg2: str, *args: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_nor(self, out: str, arg1: str, arg2: str, *args: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_xor(self, out: str, arg1: str, arg2: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_nxor(self, out: str, arg1: str, arg2: str):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_iff(self, out: str, arg: str):
        raise NotImplementedError()


class BenchToCircuit(AbstractBenchParser):
    """Parser that processes stream of .bench file lines and returns new Circuit
    object."""

    def __init__(self, *args, **kwargs):
        super(BenchToCircuit, self).__init__(*args, **kwargs)
        self._circuit = Circuit()

    def convert_to_circuit(self, stream: tp.Iterable[str]) -> Circuit:
        for _ in self.convert(stream):
            pass
        return self._circuit

    def _eof(self) -> tp.Iterable:
        """Check initializations all operands into the circuit and filling gates
        users."""
        for _, gate in self._circuit._elements.items():
            for operand in gate.operands:
                check_elements_exist((operand,), self._circuit)
                self._circuit.get_element(operand)._add_users(gate.label)
        return []

    def _add_gate(self, out: str, gate_type: GateType, arg1: str, *args: str):
        """Add gate into the circuit without checking the initialization of operands."""
        self._circuit._emplace_gate(
            label=out,
            gate_type=gate_type,
            operands=(arg1, *args),
        )
        return []

    def _process_input_gate(self, line: str) -> list:
        """Parses line with input gate."""
        _gate = line[6:].strip(') \n')
        logger.debug(f'\tAdding input gate: {_gate}')
        self._circuit._emplace_gate(_gate, INPUT)
        return []

    def _process_output_gate(self, line: str) -> list:
        """Parses line with output gate."""
        _gate = line[7:].strip(') \n')
        logger.debug(f'\tAdding output gate: {_gate}')
        self._circuit._outputs.append(_gate)
        return []

    def _process_not(self, out: str, arg: str):
        return self._add_gate(out, NOT, arg)

    def _process_xor(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, XOR, arg1, arg2, *args)

    def _process_nxor(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, NXOR, arg1, arg2, *args)

    def _process_or(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, OR, arg1, arg2, *args)

    def _process_nor(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, NOR, arg1, arg2, *args)

    def _process_and(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, AND, arg1, arg2, *args)

    def _process_nand(self, out: str, arg1: str, arg2: str, *args: str):
        return self._add_gate(out, NAND, arg1, arg2, *args)

    def _process_iff(self, out: str, arg: str):
        return self._add_gate(out, IFF, arg)
