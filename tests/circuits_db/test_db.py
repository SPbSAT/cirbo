import pytest
import typing as tp
from io import BytesIO
from boolean_circuit_tool.core.circuit import gate, GateType, Gate
from boolean_circuit_tool.core.circuit import Circuit
from boolean_circuit_tool.circuits_db.db import CircuitsDatabase
from boolean_circuit_tool.core.logic import DontCare
from boolean_circuit_tool.circuits_db.exceptions import CircuitsDatabaseError
from boolean_circuit_tool.core.boolean_function import RawTruthTableModel

_gate_types = [
    gate.NOT,
    gate.AND,
    gate.OR,
    gate.NOR,
    gate.NAND,
    gate.XOR,
    gate.NXOR,
    gate.IFF,
    gate.GEQ,
    gate.GT,
    gate.LEQ,
    gate.LT,
    gate.ALWAYS_TRUE,
    gate.ALWAYS_FALSE,
]



def create_one_gate_circuit(gate_type: GateType) -> Circuit:
    circuit = Circuit()

    circuit.add_gate(Gate("A", gate.INPUT))
    if gate_type in [gate.NOT, gate.IFF]:
        circuit.emplace_gate("C", gate_type, ("A",))
    else:
        circuit.emplace_gate("B", gate.INPUT)
        circuit.emplace_gate("C", gate_type, ("A", "B"))
    circuit.mark_as_output("C")
    return circuit


def create_alternative_and_gate() -> Circuit:
    circuit = Circuit()
    circuit.emplace_gate("x1", gate.INPUT)
    circuit.emplace_gate("x2", gate.INPUT)
    circuit.emplace_gate("x1==x2", gate.NXOR, ("x1", "x2"))
    circuit.emplace_gate("and", gate.AND, ("x1", "x1==x2"))
    circuit.mark_as_output("and")
    assert circuit.get_truth_table() == [[False, False, False, True]]
    return circuit


def create_all_gates_db(use_label: bool) -> CircuitsDatabase:
    db = CircuitsDatabase()
    db.open()
    for gate_type in _gate_types:
        circuit = create_one_gate_circuit(gate_type)
        if not use_label and circuit.get_truth_table()[0][0]:
            # Skip not normalized circuits, as db needs ony normalized circuits
            continue
        if use_label:
            db.add_circuit(circuit, gate_type.name)
        else:
            db.add_circuit(circuit)
    return db


@pytest.mark.parametrize("use_label",
                         [
                             (False,),
                             (True,),
                         ])
def test_one_gate_db_queries(use_label):
    db = create_all_gates_db(use_label)
    for gate_type in _gate_types:
        original = create_one_gate_circuit(gate_type)
        if use_label:
            retrieved = db.get_by_label(gate_type.name)
        else:
            retrieved = db.get_by_raw_truth_table(original.get_truth_table())
        assert retrieved is not None
        assert len(original.inputs) == len(retrieved.inputs)
        assert len(original.outputs) == len(retrieved.outputs)
        assert original.get_truth_table() == retrieved.get_truth_table()


def test_add_circuit_with_existing_label_raises():
    with CircuitsDatabase() as db:
        circuit = create_one_gate_circuit(gate.NOT)
        label = "simple_circuit"
        db.add_circuit(circuit, label)
        with pytest.raises(CircuitsDatabaseError):
            db.add_circuit(circuit, label)


def test_get_by_raw_truth_table_model_works():
    with CircuitsDatabase() as db:
        circuit = create_one_gate_circuit(gate.AND)
        db.add_circuit(circuit)

        truth_table: RawTruthTableModel = [[False, False, DontCare, True]]

        retrieved_circuit = db.get_by_raw_truth_table_model(truth_table)

        assert retrieved_circuit is not None
        assert retrieved_circuit.get_truth_table() == circuit.get_truth_table()


def test_get_by_raw_truth_table_model_returns_minimal_size():
    with CircuitsDatabase() as db:
        small_circuit = create_one_gate_circuit(gate.OR)
        large_circuit = create_alternative_and_gate()
        db.add_circuit(small_circuit)
        db.add_circuit(large_circuit)
        truth_table = [[False, DontCare, DontCare, True]]
        retrieved_circuit = db.get_by_raw_truth_table_model(truth_table)
        assert len(retrieved_circuit.elements) == 3
        assert retrieved_circuit.get_truth_table() == [[False, True, True, True]]


@pytest.mark.parametrize("use_label",
                         [
                             (False,),
                             (True,),
                         ])
def test_save_and_load_database(use_label):
    db = create_all_gates_db(use_label)
    stream = BytesIO()
    db.save(stream)
    stream.seek(0)
    with CircuitsDatabase(stream) as loaded_db:
        assert db._dict == loaded_db._dict
