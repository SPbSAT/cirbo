import typing as tp

from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import NOT, OR, NOR, AND, NAND, XOR, NXOR, IFF, INPUT, Label, Gate, GateType
from boolean_circuit_tool.core.circuits_db.bit_io import BitReader, BitWriter
from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = ['encode_circuit', 'decode_circuit']

_gate_type_to_int: tp.Dict[GateType, int] = {
    NOT: 0,
    AND: 1,
    OR: 2,
    NOR: 3,
    NAND: 4,
    XOR: 5,
    NXOR: 6,
    IFF: 7
}

_int_to_gate_type: tp.Dict[int, GateType] = {val: key for key, val in _gate_type_to_int}


def encode_circuit(circuit: Circuit, basis: tp.Literal["aig", "bench"]) -> bytes:
    word_length = _get_word_length(circuit)
    encoded = bytearray()
    encoded += _encode_basis(basis)
    encoded += word_length.to_bytes(length=1, signed=False)
    bit_writer = BitWriter()
    gate_ids = _enumerate_gates(circuit)
    bit_writer.write_number(len(circuit.inputs), word_length)
    bit_writer.write_number(len(circuit.outputs), word_length)
    bit_writer.write_number(len(gate_ids) - len(circuit.inputs) - len(circuit.outputs), word_length)

    for label, identifier in gate_ids.items():
        gate = circuit.get_element(label)
        if gate.gate_type == INPUT:
            continue
        gate_type_id = _gate_type_to_int[gate.gate_type]
        if basis == "aig":
            bit_writer.write_number(gate_type_id, 1)
        else:
            bit_writer.write_number(gate_type_id, 3)
        for operand_label in gate.operands:
            bit_writer.write_number(gate_ids[operand_label], word_length)

    for label in circuit.outputs:
        bit_writer.write_number(gate_ids[label], word_length)

    encoded += bytes(bit_writer)
    return bytes(encoded)


def decode_circuit(bytes_: bytes) -> Circuit:
    byte_array = bytearray(bytes_)
    basis_byte = byte_array[0]
    basis = "aig" if basis_byte == 0 else "bench" if basis_byte == 1 else None

    if basis is None:
        raise BooleanCircuitToolError("Unsupported basis in encoded data")

    word_length = byte_array[1]
    bit_reader = BitReader(bytes(byte_array[2:]))
    num_inputs = bit_reader.read_number(word_length)
    num_outputs = bit_reader.read_number(word_length)
    num_gates = bit_reader.read_number(word_length)

    circuit = Circuit()

    gate_labels: tp.Dict[int, Label] = dict()

    for i in range(num_inputs):
        label = f"input_{i}"
        circuit.emplace_gate(label, INPUT)
        gate_labels[i] = label

    for _ in range(num_gates):
        if basis == "aig":
            gate_type_id = bit_reader.read_number(1)
        else:
            gate_type_id = bit_reader.read_number(3)

        gate_type = _int_to_gate_type.get(gate_type_id)
        if gate_type is None:
            raise BooleanCircuitToolError(f"Invalid gate type id {gate_type_id}")

        operands: tp.List[str] = []
        for i in range(_get_arity(gate_type)):
            gate_id = bit_reader.read_number(word_length)
            label = gate_labels.setdefault(gate_id, f"gate_{len(gate_labels)}")
            operands.append(label)

        gate_id = len(gate_labels)
        label = Label(f"gate_{gate_id}")
        circuit.emplace_gate(label, gate_type, tuple(operands))
        gate_labels[gate_id] = label

    for _ in range(num_outputs):
        gate_id = bit_reader.read_number(word_length)
        circuit.mark_as_output(gate_labels[gate_id])

    return circuit


def _encode_basis(basis: tp.Literal["aig", "bench"]) -> bytes:
    if basis == "aig":
        return b"\x00"
    elif basis == "bench":
        return b"\x01"
    else:
        assert False, f"Basis: {basis} is unsupported"


def _get_word_length(circuit: Circuit) -> int:
    if circuit.elements_number == 0:
        return 1
    else:
        return (circuit.elements_number - 1).bit_length()


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
