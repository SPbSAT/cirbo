import pytest
from boolean_circuit_tool.circuits_db.circuits_encoding import (
    decode_circuit,
    encode_circuit,
)
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.core.circuit.gate import (
    AND,
    Gate,
    GEQ,
    GT,
    IFF,
    INPUT,
    LEQ,
    LT,
    NAND,
    NOR,
    NOT,
    NXOR,
    OR,
    XOR,
)


def create_test_circuit(gates):
    circuit = Circuit()
    for label, gate_type, operands in gates:
        circuit.add_gate(Gate(label, gate_type, operands))
    for label, gate_type, _ in gates[-3:]:
        circuit.mark_as_output(label)
    return circuit


@pytest.mark.parametrize(
    "gates",
    [
        [],
        # Simple circuits
        [("A", INPUT, ()), ("B", NOT, ("A",)), ("C", AND, ("A", "B"))],
        [("A", INPUT, ()), ("B", NOT, ("A",)), ("C", OR, ("A", "B"))],
        # Complex circuit with multiple gate types (XAIG basis)
        [
            ("A", INPUT, ()),
            ("B", INPUT, ()),
            ("C", AND, ("A", "B")),
            ("D", OR, ("A", "B")),
            ("E", NOR, ("A", "B")),
            ("F", NAND, ("A", "B")),
            ("G", XOR, ("A", "B")),
            ("H", NXOR, ("A", "B")),
            ("I", IFF, ("A",)),
            ("J", GEQ, ("A", "B")),
            ("K", GT, ("A", "B")),
            ("L", LEQ, ("A", "B")),
            ("M", LT, ("A", "B")),
            ("N", NOT, ("A")),
        ],
        # Circuit with only AND and NOT gates (AIG basis)
        [
            ("A", INPUT, ()),
            ("B", NOT, ("A",)),
            ("C", AND, ("A", "B")),
            ("D", NOT, ("C",)),
            ("E", AND, ("B", "D")),
        ],
    ],
)
def test_encode_decode_circuit(gates):
    circuit = create_test_circuit(gates)
    encoded = encode_circuit(circuit)
    decoded = decode_circuit(encoded)

    assert decoded.gates_number() == circuit.gates_number()
    assert len(decoded.inputs) == len(circuit.inputs)
    assert len(decoded.outputs) == len(circuit.outputs)
    original_truth_table = circuit.get_truth_table()
    decoded_truth_table = decoded.get_truth_table()
    assert original_truth_table == decoded_truth_table


@pytest.mark.parametrize(
    "gates, expected_word_size",
    [
        ([("A", INPUT, ())], 1),
        ([("A", INPUT, ()), ("B", AND, ("A", "A"))], 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", AND, ("A", "B"))], 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", OR, ("A", "B"))], 2),
        (
            [
                ("A", INPUT, ()),
                ("B", AND, ("A", "A")),
                ("C", XOR, ("A", "B")),
                ("D", LT, ("C", "B")),
            ],
            2,
        ),
        (
            [
                ("A", INPUT, ()),
                ("B", AND, ("A", "A")),
                ("C", XOR, ("A", "B")),
                ("D", LT, ("C", "B")),
                ("E", LT, ("C", "D")),
            ],
            3,
        ),
    ],
)
def test_word_size_is_optimal(gates, expected_word_size):
    from boolean_circuit_tool.circuits_db.circuits_encoding import _get_word_size

    circuit = create_test_circuit(gates)
    encoded = encode_circuit(circuit)
    decoded = decode_circuit(encoded)
    assert _get_word_size(decoded) == expected_word_size
