"""Implementation of .bench parsing."""

import abc
import logging
import typing as tp

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.exceptions import CircuitValidationError
from boolean_circuit_tool.core.gate import GateLabel, GateType
from boolean_circuit_tool.core.parser.abstract import AbstractParser
from boolean_circuit_tool.core.utils.validation import check_init_gates


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
    Since some operators could be defined using others, minimal complete
    definition of class is:
        _process_iff(...);
        _process_and(...);
        _process_or(...);
        _process_xor(...);
        _eof(...).

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
        self._processings: tp.Dict[str, tp.Callable] = {
            GateType.NOT.value: self._process_not,
            GateType.AND.value: self._process_and,
            GateType.NAND.value: self._process_nand,
            GateType.OR.value: self._process_or,
            GateType.NOR.value: self._process_nor,
            GateType.XOR.value: self._process_xor,
            GateType.NXOR.value: self._process_nxor,
            GateType.IFF.value: self._process_iff,
            GateType.BUFF.value: self._process_iff,
            GateType.MUX.value: self._process_mux,
        }

    def _process_line(self, line: str) -> tp.Iterable[str]:
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

    def _parse_operator_gate(self, line: str) -> tp.Tuple[str, int, tp.List[int]]:
        """
        Parses line with operator gate.

        :returns (operator: str, result_gate: int, operands: List[int]).

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

    def _process_nand(self, out: int, arg1: int, arg2: int, *args: int):
        return self._process_and(-out, arg1, arg2, *args)

    def _process_nor(self, out: int, arg1: int, arg2: int, *args: int):
        return self._process_or(-out, arg1, arg2, *args)

    def _process_nxor(self, out: int, arg1: int, arg2: int):
        return self._process_xor(-out, arg1, arg2)

    @abc.abstractmethod
    def _process_input_gate(self, line: str) -> list:
        """Parses line with input gate."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_output_gate(self, line: str) -> list:
        """Parses line with output gate."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_not(self, out: int, arg: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_and(self, out: int, arg1: int, arg2: int, *args: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_or(self, out: int, arg1: int, arg2: int, *args: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_xor(self, out: int, arg1: int, arg2: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_iff(self, out: int, arg: int):
        raise NotImplementedError()

    @abc.abstractmethod
    def _process_mux(self, out: int, arg1: int, arg2: int, arg3: int):
        raise NotImplementedError()


class BenchToCircuit(AbstractBenchParser):
    """Parser that processes stream of .bench file lines and returns new Circuit
    object."""

    def __init__(self, *args, **kwargs):
        super(BenchToCircuit, self).__init__(*args, **kwargs)
        self._circuit = Circuit()

    def convert_to_circuit(self, stream: tp.Iterable) -> Circuit:
        for _ in self.convert(stream):
            pass
        return self._circuit

    def _eof(self) -> tp.Iterable:
        """Check initializations all operands into the circuit."""
        for _, gate in self._circuit.gates.items():
            res = check_init_gates(tuple(gate.operands), self._circuit)
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
        self._circuit._emplace_gate(_gate, GateType.INPUT)
        return []

    def _process_output_gate(self, line: str) -> list:
        """Parses line with output gate."""
        _gate = line[7:].strip(') \n')
        logger.debug(f'\tAdding output gate: {_gate}')
        self._circuit.output_gates.add(_gate)
        return []

    def _process_not(self, out: int, arg: int):
        return self._add_gate(out, GateType.NOT, arg)

    def _process_xor(self, out: int, arg1: int, arg2: int):
        return self._add_gate(out, GateType.XOR, arg1, arg2)

    def _process_nxor(self, out: int, arg1: int, arg2: int):
        return self._add_gate(out, GateType.NXOR, arg1, arg2)

    def _process_or(self, out: int, arg1: int, arg2: int, *args: int):
        return self._add_gate(out, GateType.OR, arg1, arg2, *args)

    def _process_nor(self, out: int, arg1: int, arg2: int, *args: int):
        return self._add_gate(out, GateType.NOR, arg1, arg2, *args)

    def _process_and(self, out: int, arg1: int, arg2: int, *args: int):
        return self._add_gate(out, GateType.AND, arg1, arg2, *args)

    def _process_nand(self, out: int, arg1: int, arg2: int, *args: int):
        return self._add_gate(out, GateType.NAND, arg1, arg2, *args)

    def _process_iff(self, out: int, arg: int):
        return self._add_gate(out, GateType.IFF, arg)

    def _process_mux(self, out: int, arg1: int, arg2: int, arg3: int):
        return self._add_gate(out, GateType.MUX, arg1, arg2, arg3)
