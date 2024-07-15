import typing as tp
from pathlib import Path

from boolean_circuit_tool.core.circuits_db.binary_dict_io import BinaryDictReader
from boolean_circuit_tool.core.circuits_db.circuits_coding import encode_circuit, decode_circuit
from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = ['CircuitsDatabase']


class CircuitsDatabase:
    def __init__(self, db_file: tp.Optional[Path] = None):
        self.dict = BinaryDictReader(db_file) if db_file is not None else dict()

    def get_by_label(self, label: str) -> tp.Optional[Circuit]:
        encoded_circuit = self.dict.get(label)
        if encoded_circuit is None:
            return None
        return decode_circuit(encoded_circuit)

    def add_circuit(self, circuit: Circuit, label: tp.Optional[str] = None,
                    basis: tp.Literal["aig", "bench"] = "bench") -> None:
        if label is None:
            label = self._generate_label(circuit)
        encoded_circuit = encode_circuit(circuit, basis)
        if label in self.dict.keys():
            raise BooleanCircuitToolError(f"Label: {label} is already in Circuits Database")
        self.dict[label] = encoded_circuit

    def get_by_truth_table(self, truth_table) -> tp.Optional[Circuit]:
        # TODO: typehint once truth_table is merged
        label = self._generate_label(truth_table)
        return self.get_by_label(label)

    def _generate_label(self, boolean_function):
        # TODO: generate label using truth table of given boolean_function (Protocol)
        raise NotImplementedError()
