"""
This module provides functionality for encoding and decoding boolean circuits to and
from a binary format.

Binary File Specification for Encoding and Decoding Circuits:

The binary file consists of a header, followed by circuit parameters, and the circuit body.

File Structure:
1. Header
    - Word Size (1 byte):
        Defines the word size in bits used for encoding numbers in the file.

2. Circuit Parameters
    - Number of Inputs (word_size bits):
        The number of input gates in the circuit.
    - Number of Outputs (word_size bits):
        The number of output gates in the circuit.
    - Number of Intermediate Gates (word_size bits):
        The number of intermediate gates in the circuit
    (total gates - input gates).

3. Circuit Body
    - Gates:
        - For each gate (excluding inputs):
            - Gate Type (4 bits): Encodes the type of gate.
                The mapping is defined in `_gate_type_to_int` and `_int_to_gate_type`.
            - Operands (word_size bits each):
                References to the gates that are inputs to this gate.
                The number of operands depends on the gate type.
    - Outputs:
        - For each output gate:
            - Gate Identifier (word_size bits):
                Reference to the gate that is an output.

Gate Type Encoding:
- NOT: 0
- AND: 1
- OR: 2
- NOR: 3
- NAND: 4
- XOR: 5
- NXOR: 6
- IFF: 7
- GEQ: 8
- GT: 9
- LEQ: 10
- LT: 11
- ALWAYS_TRUE: 12
- ALWAYS_FALSE: 13

"""

import typing as tp

from boolean_circuit_tool.circuits_db.bit_io import BitReader, BitWriter
from boolean_circuit_tool.circuits_db.exceptions import CircuitEncodingError

from boolean_circuit_tool.core.circuit import Circuit, gate
from boolean_circuit_tool.core.circuit.gate import Gate, GateType, Label

__all__ = ['encode_circuit', 'decode_circuit']

# Number of bits used to encode the gate type
GATE_TYPE_BIT_SIZE = 4


def encode_circuit(circuit: Circuit) -> bytes:
    """
    Encode a circuit into bytes.

    :param circuit: The circuit to encode.
    :return: The encoded circuit as bytes.

    """
    word_size = _get_word_size(circuit)
    bit_writer = BitWriter()
    _encode_header(bit_writer, word_size)
    _encode_circuit_parameters(bit_writer, word_size, circuit)
    _encode_circuit_body(bit_writer, word_size, circuit)
    return bytes(bit_writer)


def decode_circuit(bytes_: bytes) -> Circuit:
    """
    Decode a circuit from bytes.

    :param bytes_: The bytes to decode.
    :return: The decoded circuit.

    """
    bit_reader = BitReader(bytes_)
    word_size = _decode_header(bit_reader)
    inputs_count, outputs_count, intermediates_count = _decode_circuit_parameters(
        bit_reader, word_size
    )
    circuit = Circuit()
    _decode_circuit_body(
        bit_reader, word_size, inputs_count, outputs_count, intermediates_count, circuit
    )
    return circuit


def _encode_header(bit_writer: BitWriter, word_size: int) -> None:
    bit_writer.write_byte(word_size)


def _decode_header(bit_reader: BitReader) -> int:
    word_size = bit_reader.read_byte()
    return word_size


def _encode_circuit_parameters(
        bit_writer: BitWriter, word_size: int, circuit: Circuit
) -> None:
    bit_writer.write_number(len(circuit.inputs), word_size)
    bit_writer.write_number(len(circuit.outputs), word_size)
    bit_writer.write_number(circuit.gates_number([gate.INPUT]), word_size)


def _decode_circuit_parameters(
        bit_reader: BitReader, word_size: int
) -> tp.Tuple[int, int, int]:
    inputs_count = bit_reader.read_number(word_size)
    outputs_count = bit_reader.read_number(word_size)
    intermediates_count = bit_reader.read_number(word_size)
    return inputs_count, outputs_count, intermediates_count


def _encode_gate(
        bit_writer: BitWriter,
        gate_: Gate,
        gate_identifiers: tp.Dict[str, int],
        word_size: int,
):
    if gate_.gate_type == gate.INPUT:
        return
    gate_type_id = _gate_type_to_int.get(gate_.gate_type)
    if gate_type_id is None:
        raise CircuitEncodingError("Tried to encode unsupported gate type")
    bit_writer.write_number(gate_type_id, GATE_TYPE_BIT_SIZE)
    for operand_label in gate_.operands:
        bit_writer.write_number(gate_identifiers[operand_label], word_size)


def _generate_label(gate_id: int) -> Label:
    return f"gate_{gate_id}"


def _decode_gate(
        bit_reader: BitReader, word_size: int, gates: tp.Dict[int, Gate], circuit: Circuit
) -> None:
    gate_type_id = bit_reader.read_number(GATE_TYPE_BIT_SIZE)
    gate_type = _int_to_gate_type.get(gate_type_id)
    if gate_type is None:
        raise CircuitEncodingError("Tried to decode undefined gate type")
    operands: tp.List[Label] = []
    gate_id = len(gates)
    label = _generate_label(gate_id)
    for _ in range(_get_arity(gate_type)):
        arg_gate_id = bit_reader.read_number(word_size)
        arg_gate = gates.get(arg_gate_id)
        if arg_gate is None:
            raise CircuitEncodingError("Invalid argument gate identifier")
        operands.append(arg_gate.label)
    gate = Gate(label, gate_type, tuple(operands))
    gates[gate_id] = gate
    circuit.add_gate(gate)


def _encode_circuit_body(
        bit_writer: BitWriter, word_size: int, circuit: Circuit
) -> None:
    gate_identifiers = _enumerate_gates(circuit)

    for label in gate_identifiers.keys():
        _encode_gate(
            bit_writer, circuit.get_gate(label), gate_identifiers, word_size
        )

    for label in circuit.outputs:
        bit_writer.write_number(gate_identifiers[label], word_size)


def _decode_circuit_body(
        bit_reader: BitReader,
        word_size: int,
        inputs_count: int,
        outputs_count: int,
        intermediates_count: int,
        circuit: Circuit,
) -> None:
    gates: tp.Dict[int, Gate] = dict()
    for i in range(inputs_count):
        gate_ = Gate(_generate_label(i), gate.INPUT)
        gates[i] = gate_
        circuit.add_gate(gate_)

    for _ in range(intermediates_count):
        _decode_gate(bit_reader, word_size, gates, circuit)

    for _ in range(outputs_count):
        output_id = bit_reader.read_number(word_size)
        circuit.mark_as_output(_generate_label(output_id))


def _get_word_size(circuit: Circuit) -> int:
    if circuit.gates_number() == 0:
        return 1
    else:
        return max(
            len(circuit.inputs), len(circuit.outputs), circuit.gates_number([]) - 1
        ).bit_length()


def _enumerate_gates(circuit: Circuit) -> tp.Dict[Label, int]:
    result: tp.Dict[Label, int] = dict()
    for input_label in circuit.inputs:
        result[input_label] = len(result)
    for gate_label, gate_ in circuit.gates.items():
        if gate_.gate_type == gate.INPUT:
            continue
        result[gate_label] = len(result)
    return result


def _get_arity(gate_type: GateType) -> int:
    if gate_type == gate.IFF or gate_type == gate.NOT:
        return 1
    else:
        return 2


_gate_type_to_int: tp.Dict[GateType, int] = {
    gate.NOT: 0,
    gate.AND: 1,
    gate.OR: 2,
    gate.NOR: 3,
    gate.NAND: 4,
    gate.XOR: 5,
    gate.NXOR: 6,
    gate.IFF: 7,
    gate.GEQ: 8,
    gate.GT: 9,
    gate.LEQ: 10,
    gate.LT: 11,
    gate.ALWAYS_TRUE: 12,
    gate.ALWAYS_FALSE: 13,
}

_int_to_gate_type: tp.Dict[int, GateType] = {
    val: key for key, val in _gate_type_to_int.items()
}
