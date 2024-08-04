import pytest
import typing as tp
from io import BytesIO
from boolean_circuit_tool.core.circuit.gate import (
    NOT, AND, OR, NOR, NAND, XOR, NXOR, IFF, GEQ, GT, LEQ, LT, INPUT, Gate, GateType
)
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.circuits_db.circuits_coding import Basis
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.circuits_db.exceptions import CircuitsDatabaseError
from boolean_circuit_tool.core.boolean_function import RawTruthTableModel

_gate_types = [NOT, AND, OR, NOR, NAND, XOR, NXOR, IFF, GEQ, GT, LEQ, LT]


def create_one_gate_circuit(gate_type: GateType) -> Circuit:
    circuit = Circuit()

    circuit.add_gate(Gate("A", INPUT))
    if gate_type in [NOT, IFF]:
        circuit.emplace_gate("C", gate_type, ("A",))
    else:
        circuit.emplace_gate("B", INPUT)
        circuit.emplace_gate("C", gate_type, ("A", "B"))
    circuit.mark_as_output("C")
    return circuit


def create_alternative_and_gate() -> Circuit:
    circuit = Circuit()
    circuit.emplace_gate("x1", INPUT)
    circuit.emplace_gate("x2", INPUT)
    circuit.emplace_gate("x1==x2", NXOR, ("x1", "x2"))
    circuit.emplace_gate("and", AND, ("x1", "x1==x2"))
    circuit.mark_as_output("and")
    assert circuit.get_truth_table() == [[False, False, False, True]]
    return circuit


def all_gate_types(basis: Basis) -> tp.Generator[GateType, None, None]:
    for gate_type in _gate_types:
        if basis == Basis.AIG and gate_type not in (AND, NOT):
            continue
        yield gate_type


def create_all_gates_db(basis: Basis, use_label: bool) -> CircuitsDatabase:
    db = CircuitsDatabase()
    db.open()
    for gate_type in all_gate_types(basis):
        circuit = create_one_gate_circuit(gate_type)
        if use_label:
            db.add_circuit(circuit, gate_type.name, basis)
        else:
            db.add_circuit(circuit, basis=basis)
    return db


@pytest.mark.parametrize("basis, use_label",
                         [
                             (Basis.XAIG, False),
                             (Basis.XAIG, True),
                             (Basis.AIG, False),
                             (Basis.AIG, True),
                         ])
def test_one_gate_db_queries(basis, use_label):
    db = create_all_gates_db(basis, use_label)
    for gate_type in all_gate_types(basis):
        original = create_one_gate_circuit(gate_type)
        if use_label:
            retrieved = db.get_by_label(gate_type.name)
        else:
            retrieved = db.get_by_raw_truth_table(original.get_truth_table())
        assert original.elements_number == retrieved.elements_number
        assert len(original.inputs) == len(retrieved.inputs)
        assert len(original.outputs) == len(retrieved.outputs)
        assert original.get_truth_table() == retrieved.get_truth_table()


def test_add_circuit_with_existing_label_raises():
    with CircuitsDatabase() as db:
        circuit = create_one_gate_circuit(NOT)
        label = "simple_circuit"
        db.add_circuit(circuit, label)
        with pytest.raises(CircuitsDatabaseError):
            db.add_circuit(circuit, label)


def test_get_by_raw_truth_table_model_works():
    with CircuitsDatabase() as db:
        circuit = create_one_gate_circuit(AND)
        db.add_circuit(circuit)

        truth_table: RawTruthTableModel = [[False, False, DontCare, True]]

        retrieved_circuit = db.get_by_raw_truth_table_model(truth_table)

        assert retrieved_circuit is not None
        assert retrieved_circuit.get_truth_table() == circuit.get_truth_table()


def test_get_by_raw_truth_table_model_returns_minimal_size():
    with CircuitsDatabase() as db:
        small_circuit = create_one_gate_circuit(OR)
        large_circuit = create_alternative_and_gate()
        db.add_circuit(small_circuit)
        db.add_circuit(large_circuit)
        truth_table = [[False, DontCare, DontCare, True]]
        retrieved_circuit = db.get_by_raw_truth_table_model(truth_table)
        assert len(retrieved_circuit.elements) == 3
        assert retrieved_circuit.get_truth_table() == [[False, True, True, True]]


@pytest.mark.parametrize("basis, use_label",
                         [
                             (Basis.XAIG, False),
                             (Basis.XAIG, True),
                             (Basis.AIG, False),
                             (Basis.AIG, True),
                         ])
def test_save_and_load_database(basis, use_label):
    db = create_all_gates_db(basis, use_label)
    stream = BytesIO()
    db.save(stream)
    stream.seek(0)
    with CircuitsDatabase(stream) as loaded_db:
        assert db._dict == loaded_db._dict
