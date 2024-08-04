import typing as tp

from boolean_circuit_tool.core.circuit.gate import (
    NOT,
    AND,
    OR,
    NOR,
    NAND,
    XOR,
    NXOR,
    IFF,
    GEQ,
    GT,
    LEQ,
    LT,
    INPUT,
    Label,
    GateType,
    Gate,
)
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.circuits_db.bit_io import BitReader, BitWriter
from boolean_circuit_tool.circuits_db.exceptions import CircuitCodingError
from enum import Enum

__all__ = ['encode_circuit', 'decode_circuit', 'Basis']


class Basis(Enum):
    XAIG = 'xaig'
    AIG = 'aig'


def encode_circuit(circuit: Circuit, basis: tp.Union[str, Basis]) -> bytes:
    basis = Basis(basis)
    word_size = _get_word_size(circuit)
    bit_writer = BitWriter()
    _encode_header(bit_writer, basis, word_size)
    _ecode_circuit_parameters(bit_writer, word_size, circuit)
    _encode_circuit_body(bit_writer, basis, word_size, circuit)
    return bytes(bit_writer)


def decode_circuit(bytes_: bytes) -> Circuit:
    bit_reader = BitReader(bytes_)
    basis, word_size = _decode_header(bit_reader)
    inputs_count, outputs_count, intermediates_count = _decode_circuit_parameters(bit_reader, word_size)
    circuit = Circuit()
    _decode_circuit_body(bit_reader, basis, word_size, inputs_count, outputs_count, intermediates_count, circuit)
    return circuit


def _encode_header(bit_writer: BitWriter, basis: Basis, word_size: int) -> None:
    bit_writer.write_byte(_encode_basis(basis))
    bit_writer.write_byte(word_size)


def _decode_header(bit_reader: BitReader) -> tp.Tuple[Basis, int]:
    basis = _decode_basis(bit_reader.read_byte())
    word_size = bit_reader.read_byte()
    return basis, word_size


def _ecode_circuit_parameters(bit_writer: BitWriter, word_size: int, circuit: Circuit) -> None:
    bit_writer.write_number(len(circuit.inputs), word_size)
    bit_writer.write_number(len(circuit.outputs), word_size)
    bit_writer.write_number(circuit.elements_number - len(circuit.inputs), word_size)


def _decode_circuit_parameters(bit_reader: BitReader, word_size: int) -> tp.Tuple[int, int, int]:
    inputs_count = bit_reader.read_number(word_size)
    outputs_count = bit_reader.read_number(word_size)
    intermediates_count = bit_reader.read_number(word_size)
    return inputs_count, outputs_count, intermediates_count


def _encode_gate(bit_writer: BitWriter,
                 gate_bit_size: int,
                 gate: Gate,
                 gate_identifiers: tp.Dict[str, int],
                 word_size: int):
    if gate.gate_type == INPUT:
        return
    gate_type_id = _gate_type_to_int.get(gate.gate_type)
    if gate_type_id is None:
        raise CircuitCodingError("Tried to encode unsupported gate type")
    bit_writer.write_number(gate_type_id, gate_bit_size)
    for operand_label in gate.operands:
        bit_writer.write_number(gate_identifiers[operand_label], word_size)


def _generate_label(gate_id: int) -> Label:
    return f"gate_{gate_id}"


def _decode_gate(bit_reader: BitReader, gate_bit_size: int, word_size: int, gates: tp.Dict[int, Gate],
                 circuit: Circuit) -> None:
    gate_type_id = bit_reader.read_number(gate_bit_size)
    gate_type = _int_to_gate_type.get(gate_type_id)
    if gate_type is None:
        raise CircuitCodingError("Tried to decode undefined gate type")
    operands: tp.List[Label] = []
    gate_id = len(gates)
    label = _generate_label(gate_id)
    for _ in range(_get_arity(gate_type)):
        arg_gate_id = bit_reader.read_number(word_size)
        arg_gate = gates.get(arg_gate_id)
        if arg_gate is None:
            raise CircuitCodingError("Invalid argument gate identifier")
        operands.append(arg_gate.label)
    gate = Gate(label, gate_type, tuple(operands))
    gates[gate_id] = gate
    circuit.add_gate(gate)


def _encode_circuit_body(bit_writer: BitWriter, basis: Basis, word_size: int, circuit: Circuit) -> None:
    gate_identifiers = _enumerate_gates(circuit)
    gate_bit_size = _get_gate_bit_size(basis)

    for label in gate_identifiers.keys():
        _encode_gate(bit_writer, gate_bit_size, circuit.get_element(label), gate_identifiers, word_size)

    for label in circuit.outputs:
        bit_writer.write_number(gate_identifiers[label], word_size)


def _decode_circuit_body(bit_reader: BitReader,
                         basis: Basis,
                         word_size: int,
                         inputs_count: int,
                         outputs_count: int,
                         intermediates_count: int,
                         circuit: Circuit) -> None:
    gates: tp.Dict[int, Gate] = dict()
    gate_bit_size = _get_gate_bit_size(basis)
    for i in range(inputs_count):
        gate = Gate(_generate_label(i), INPUT)
        gates[i] = gate
        circuit.add_gate(gate)

    for _ in range(intermediates_count):
        _decode_gate(bit_reader, gate_bit_size, word_size, gates, circuit)

    for _ in range(outputs_count):
        output_id = bit_reader.read_number(word_size)
        circuit.mark_as_output(_generate_label(output_id))


def _encode_basis(basis: Basis) -> int:
    return {
        Basis.XAIG: 0,
        Basis.AIG: 1,
    }[basis]


def _decode_basis(encoded_basis: int) -> Basis:
    return {
        0: Basis.XAIG,
        1: Basis.AIG,
    }[encoded_basis]


def _get_gate_bit_size(basis: Basis) -> int:
    return {
        Basis.XAIG: 4,
        Basis.AIG: 1
    }[basis]


def _get_word_size(circuit: Circuit) -> int:
    if circuit.elements_number == 0:
        return 1
    else:
        return max(len(circuit.inputs), len(circuit.outputs), circuit.elements_number - 1).bit_length()


def _enumerate_gates(circuit: Circuit) -> tp.Dict[Label, int]:
    result: tp.Dict[Label, int] = dict()
    for input_label in circuit.inputs:
        result[input_label] = len(result)
    for gate_label, gate in circuit._elements.items():  # TODO: ask to create circuit.elements property to get all gates
        if gate.gate_type == INPUT:
            continue
        result[gate_label] = len(result)
    return result


def _get_arity(gate_type: GateType) -> int:
    if gate_type == IFF or gate_type == NOT:
        return 1
    else:
        return 2


_gate_type_to_int: tp.Dict[GateType, int] = {
    NOT: 0,
    AND: 1,
    OR: 2,
    NOR: 3,
    NAND: 4,
    XOR: 5,
    NXOR: 6,
    IFF: 7,
    GEQ: 8,
    GT: 9,
    LEQ: 10,
    LT: 11,
}

_int_to_gate_type: tp.Dict[int, GateType] = {val: key for key, val in _gate_type_to_int.items()}
