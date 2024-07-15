import typing as tp
from pathlib import Path
from typing import Union, Tuple, List

from boolean_circuit_tool.core.circuits_db.binary_dict_io import BinaryDictReader, BinaryDictWriter
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
        outputs_permutation = None
        if label is None:
            truth_table: tp.List[tp.List[bool]] = None  # TODO: circuit.get_truth_table()
            ordered_truth_table, outputs_permutation = _normalize_outputs_order(truth_table)
            label = str(truth_table)  # TODO: check format, maybe create better labeling
        circuit = _permute_circuit_outputs(circuit, outputs_permutation)
        encoded_circuit = encode_circuit(circuit, basis)
        if label in self.dict.keys():
            raise BooleanCircuitToolError(f"Label: {label} is already in Circuits Database")
        self.dict[label] = encoded_circuit

    def get_by_truth_table(self, truth_table) -> tp.Optional[Circuit]:
        # TODO: typehint once truth_table is merged
        truth_table: tp.List[tp.List[bool]] = None  # TODO: circuit.get_truth_table()
        ordered_truth_table, outputs_permutation = _normalize_outputs_order(truth_table)
        label = str(truth_table)  # TODO: check format, maybe create better labeling
        circuit = self.get_by_label(label)
        circuit = _permute_circuit_outputs(circuit, _invert_permutation(outputs_permutation))
        return self.get_by_label(label)

    def get_dont_cares(self, truth_table) -> Circuit:
        # TODO: how the table is presented?
        raise NotImplementedError()

    def save_to_file(self, file: Path) -> None:
        writer = BinaryDictWriter(file)
        writer.write(self.dict)


def _normalize_outputs_order(truth_table: tp.List[tp.List[bool]]) \
        -> tuple[list[list[bool]], list[int]]:
    numbered_truth_tables = [(table, i) for i, table in enumerate(truth_table)]
    numbered_truth_tables.sort()
    result_truth_tables = list(table for table, _ in numbered_truth_tables)
    result_permutation = list(i for _, i in numbered_truth_tables)
    return result_truth_tables, result_permutation


def _permute_circuit_outputs(circuit: Circuit, permutation: tp.Optional[tp.List[int]]) -> Circuit:
    # TODO: how to permute outputs in circuit?
    raise NotImplementedError()


def _invert_permutation(permutation: tp.List[int]) -> tp.List[int]:
    # TODO
    raise NotImplementedError()
