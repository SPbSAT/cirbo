import pytest
from boolean_circuit_tool.core.circuit.gate import (
    NOT, AND, OR, NOR, NAND, XOR, NXOR, IFF, GEQ, GT, LEQ, LT, INPUT, Gate
)
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.circuits_db.circuits_coding import (
    encode_circuit, decode_circuit, Basis
)


def create_test_circuit(gates):
    circuit = Circuit()
    for label, gate_type, operands in gates:
        circuit.add_gate(Gate(label, gate_type, operands))
    for label, gate_type, _ in gates[-3:]:
        circuit.mark_as_output(label)
    return circuit


@pytest.mark.parametrize(
    "gates, basis",
    [
        # Empty circuits
        ([], Basis.AIG),
        ([], Basis.XAIG),

        # Simple circuits
        ([("A", INPUT, ()), ("B", NOT, ("A",)), ("C", AND, ("A", "B"))], Basis.AIG),
        ([("A", INPUT, ()), ("B", NOT, ("A",)), ("C", OR, ("A", "B"))], Basis.XAIG),

        # Complex circuit with multiple gate types (XAIG basis)
        ([("A", INPUT, ()), ("B", INPUT, ()), ("C", AND, ("A", "B")), ("D", OR, ("A", "B")),
          ("E", NOR, ("A", "B")), ("F", NAND, ("A", "B")), ("G", XOR, ("A", "B")),
          ("H", NXOR, ("A", "B")), ("I", IFF, ("A",)), ("J", GEQ, ("A", "B")),
          ("K", GT, ("A", "B")), ("L", LEQ, ("A", "B")), ("M", LT, ("A", "B")), ("N", NOT, ("A"))], Basis.XAIG),

        # Circuit with only AND and NOT gates (AIG basis)
        ([("A", INPUT, ()), ("B", NOT, ("A",)), ("C", AND, ("A", "B")),
          ("D", NOT, ("C",)), ("E", AND, ("B", "D"))], Basis.AIG),
    ]
)
def test_encode_decode_circuit(gates, basis):
    circuit = create_test_circuit(gates)
    encoded = encode_circuit(circuit, basis)
    decoded = decode_circuit(encoded)

    assert decoded.elements_number == circuit.elements_number
    assert len(decoded.inputs) == len(circuit.inputs)
    assert len(decoded.outputs) == len(circuit.outputs)
    original_truth_table = circuit.get_truth_table()
    decoded_truth_table = decoded.get_truth_table()
    assert original_truth_table == decoded_truth_table


@pytest.mark.parametrize(
    "gates, basis, expected_word_size",
    [
        ([("A", INPUT, ())], Basis.AIG, 1),
        ([("A", INPUT, ()), ("B", AND, ("A", "A"))], Basis.AIG, 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", AND, ("A", "B"))], Basis.AIG, 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", OR, ("A", "B"))], Basis.XAIG, 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", XOR, ("A", "B")), ("D", LT, ("C", "B"))], Basis.XAIG, 2),
        ([("A", INPUT, ()), ("B", AND, ("A", "A")), ("C", XOR, ("A", "B")), ("D", LT, ("C", "B")),
          ("E", LT, ("C", "D"))], Basis.XAIG, 3),
    ]
)
def test_word_size_is_optimal(gates, basis, expected_word_size):
    from boolean_circuit_tool.circuits_db.circuits_coding import _get_word_size
    circuit = create_test_circuit(gates)
    encoded = encode_circuit(circuit, basis)
    decoded = decode_circuit(encoded)
    word_size = _get_word_size(decoded)
    assert word_size == expected_word_size
