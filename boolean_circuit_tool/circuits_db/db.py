import copy
import typing as tp
from pathlib import Path

from boolean_circuit_tool.circuits_db.binary_dict_io import read_binary_dict, write_binary_dict
from boolean_circuit_tool.circuits_db.circuits_coding import encode_circuit, decode_circuit
from boolean_circuit_tool.core.circuit.circuit import Circuit
from boolean_circuit_tool.circuits_db.exceptions import CircuitsDatabaseError
from boolean_circuit_tool.core.boolean_function import RawTruthTable

__all__ = ['CircuitsDatabase']


class CircuitsDatabase:
    def __init__(self, db_file: tp.Optional[Path] = None):
        self._dict = read_binary_dict(db_file) if db_file is not None else dict()

    def get_by_label(self, label: str) -> tp.Optional[Circuit]:
        encoded_circuit = self._dict.get(label)
        if encoded_circuit is None:
            return None
        return decode_circuit(encoded_circuit)

    def add_circuit(self, circuit: Circuit, label: tp.Optional[str] = None,
                    basis: tp.Literal["aig", "bench"] = "bench") -> None:
        if label is None:
            truth_table = circuit.get_truth_table()
            ordered_truth_table, outputs_permutation = _normalize_outputs_order(truth_table)
            label = _truth_table_to_label(ordered_truth_table)
            circuit = copy.deepcopy(circuit)
            _permute_circuit_outputs(circuit, outputs_permutation)
        encoded_circuit = encode_circuit(circuit, basis)
        if label in self._dict.keys():
            raise CircuitsDatabaseError(f"Label: {label} is already in Circuits Database")
        self._dict[label] = encoded_circuit

    def get_by_truth_table(self, truth_table: RawTruthTable) -> tp.Optional[Circuit]:
        ordered_truth_table, outputs_permutation = _normalize_outputs_order(truth_table)
        label = _truth_table_to_label(ordered_truth_table)
        circuit = self.get_by_label(label)
        if circuit is None:
            return None
        _permute_circuit_outputs(circuit, _invert_permutation(outputs_permutation))
        return circuit

    def get_dont_cares(self, truth_table) -> Circuit:
        # TODO: how the table is presented?
        raise NotImplementedError()

    def save_to_file(self, file: Path) -> None:
        write_binary_dict(self._dict, file)


def _normalize_outputs_order(truth_table: RawTruthTable) \
        -> tuple[RawTruthTable, list[int]]:
    numbered_truth_tables = [(table, i) for i, table in enumerate(truth_table)]
    numbered_truth_tables.sort()
    result_truth_tables = list(table for table, _ in numbered_truth_tables)
    result_permutation = list(i for _, i in numbered_truth_tables)
    return result_truth_tables, result_permutation


def _permute_circuit_outputs(circuit: Circuit, permutation: tp.List[int]) -> None:
    new_outputs = _apply_permutation(circuit.outputs, permutation)
    circuit.order_outputs(new_outputs)


def _invert_permutation(permutation: tp.List[int]) -> tp.List[int]:
    inverse = [0] * len(permutation)
    for i, p in enumerate(permutation):
        inverse[p] = i
    return inverse


T = tp.TypeVar('T')


def _apply_permutation(data: tp.List[T], permutation: tp.List[int]) -> tp.List[T]:
    return [data[i] for i in permutation]


def _truth_table_to_label(truth_table: RawTruthTable) -> str:
    str_truth_tables = [''.join(str(int(i)) for i in table)
                        for table in truth_table]
    return '_'.join(str_truth_tables)
