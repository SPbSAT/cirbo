import io
import itertools
import lzma
import typing as tp
from pathlib import Path

import typing_extensions as tp_ext

from cirbo.circuits_db.binary_dict_io import read_binary_dict, write_binary_dict
from cirbo.circuits_db.circuits_encoding import decode_circuit, encode_circuit
from cirbo.circuits_db.exceptions import (
    CircuitDatabaseCloseError,
    CircuitDatabaseNotOpenedError,
    CircuitDatabaseOpenError,
    CircuitsDatabaseError,
)
from cirbo.circuits_db.normalization import NormalizationInfo
from cirbo.core.boolean_function import RawTruthTable, RawTruthTableModel
from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.gate import GateType, IFF, INPUT, NOT
from cirbo.core.logic import DontCare

__all__ = ['CircuitsDatabase']


class CircuitsDatabase:
    """
    A class to manage a database of circuits.

    The CircuitsDatabase class allows for storing, retrieving, and manipulating boolean
    circuits. It supports operations such as opening and closing the database, adding
    circuits, and querying circuits based on labels and truth tables.

    """

    def __init__(self, db_source: tp.Optional[tp.Union[tp.BinaryIO, Path, str]] = None):
        self._db_source = db_source
        self._dict: tp.Optional[tp.Dict[str, bytes]] = None

    def open(self) -> None:
        """
        Open the database for operations.

        :raises CircuitDatabaseOpenError: If the database is already opened or the
            source type is unsupported.

        """
        if self._dict is not None:
            raise CircuitDatabaseOpenError("Try to open already opened database")
        if isinstance(self._db_source, str):
            self._db_source = Path(self._db_source)
        if self._db_source is None:
            self._dict = dict()
        elif isinstance(self._db_source, Path):
            if self._db_source.suffix == '.xz':
                with lzma.open(self._db_source, "rb") as lzma_file:
                    self._dict = read_binary_dict(lzma_file)
            elif self._db_source.suffix == ".bin":
                with self._db_source.open('rb') as stream:
                    self._dict = read_binary_dict(stream)
            else:
                raise CircuitDatabaseOpenError(
                    f"Try to open database from unsupported file: "
                    f"{self._db_source.suffix}"
                )
        elif isinstance(self._db_source, io.BytesIO):
            self._db_source.seek(0)
            self._dict = read_binary_dict(self._db_source)
        else:
            raise CircuitDatabaseOpenError("Unsupported db source type")

    def close(self) -> None:
        """
        Close the database, releasing any resources.

        :raises CircuitDatabaseCloseError: If the database is already closed.

        """
        if self._dict is None:
            raise CircuitDatabaseCloseError("Try to close already closed database")
        self._dict = None

    def __enter__(self) -> tp_ext.Self:
        """
        Enter the runtime context related to this object.

        :return: The opened database instance.

        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context related to this object.

        :param exc_type: The exception type.
        :param exc_val: The exception value.
        :param exc_tb: The traceback object.

        """
        self.close()

    def get_by_label(self, label: str) -> tp.Optional[Circuit]:
        """
        Retrieve a circuit by its label.

        :param label: The label of the circuit.
        :return: The circuit if found, otherwise None.
        :raises CircuitDatabaseNotOpenedError: If the database is not opened.

        """
        if self._dict is None:
            raise CircuitDatabaseNotOpenedError()
        encoded_circuit = self._dict.get(label)
        if encoded_circuit is None:
            return None
        return decode_circuit(encoded_circuit)

    def get_by_raw_truth_table(
        self,
        truth_table: RawTruthTable,
    ) -> tp.Optional[Circuit]:
        """
        Retrieve a circuit by its raw truth table.

        :param truth_table: The raw truth table of the circuit.
        :return: The circuit if found, otherwise None.

        """
        normalization = NormalizationInfo(truth_table)
        normalized_truth_table = normalization.truth_table
        label = _truth_table_to_label(normalized_truth_table)
        circuit = self.get_by_label(label)
        if circuit is None:
            return None
        normalization.denormalize(circuit)
        return circuit

    def add_circuit(self, circuit: Circuit, label: tp.Optional[str] = None) -> None:
        """
        Add a circuit to the database.

        :param circuit: The circuit to add.
        :param label: An optional label for the circuit.
        :raises CircuitDatabaseNotOpenedError: If the database is not opened.
        :raises CircuitsDatabaseError: If the circuit is not normalized or the label
            already exists.

        """
        if self._dict is None:
            raise CircuitDatabaseNotOpenedError()
        if label is None:
            truth_table = circuit.get_truth_table()
            normalization = NormalizationInfo(truth_table)
            normalized_truth_table = normalization.truth_table
            if normalized_truth_table != truth_table:
                raise CircuitsDatabaseError("Cannot add not normalized circuit")
            label = _truth_table_to_label(normalized_truth_table)
        if label in self._dict.keys():
            raise CircuitsDatabaseError(
                f"Label: {label} is already in Circuits Database"
            )
        encoded_circuit = encode_circuit(circuit)
        self._dict[label] = encoded_circuit

    def get_by_raw_truth_table_model(
        self,
        truth_table: RawTruthTableModel,
        exclusion_list: tp.Optional[tp.Container[GateType]] = None,
    ) -> tp.Optional[Circuit]:
        """
        Retrieve a circuit by its raw truth table model.

        :param truth_table: The raw truth table model of the circuit.
        :return: The circuit if found, otherwise None.

        """
        undefined_positions: tp.Dict[int, tp.Tuple[int, int]] = dict()
        defined_truth_table: tp.List[tp.List[bool]] = [
            [False if val in [DontCare, False] else True for val in table]
            for table in truth_table
        ]
        for i, table in enumerate(truth_table):
            for j, value in enumerate(table):
                if value is not DontCare:
                    continue
                undefined_positions[len(undefined_positions)] = (i, j)
        result: tp.Optional[Circuit] = None
        result_size: tp.Optional[int] = None
        for substitution in itertools.product(
            (False, True), repeat=len(undefined_positions)
        ):
            for i, val in enumerate(substitution):
                j, k = undefined_positions[i]
                defined_truth_table[j][k] = val
            circuit = self.get_by_raw_truth_table(defined_truth_table)
            if circuit is None:
                continue
            circuit_size = circuit.gates_number(exclusion_list)
            if result_size is None or circuit_size < result_size:
                result_size = circuit_size
                result = circuit
        return result

    def save(self, stream: tp.IO[bytes]) -> None:
        """
        Save the database to a binary stream.

        :param stream: The binary stream to save the database to.
        :raises CircuitDatabaseNotOpenedError: If the database is not opened.

        """
        if self._dict is None:
            raise CircuitDatabaseNotOpenedError()
        write_binary_dict(self._dict, stream)


def _truth_table_to_label(truth_table: RawTruthTable) -> str:
    """
    Convert a truth table to a label.

    :param truth_table: The raw truth table.
    :return: The label as a string.

    """
    str_truth_tables = [''.join(str(int(i)) for i in table) for table in truth_table]
    return '_'.join(str_truth_tables)


def _get_circuit_size(circuit: Circuit) -> int:
    """
    Calculate the size of a circuit based on the number of non-trivial gates.

    :param circuit: The circuit whose size is to be calculated.
    :return: The size of the circuit.

    """
    gate_types = map(lambda x: x.gate_type, circuit.gates.values())
    nontrivial_gates = list(filter(lambda x: x not in [NOT, IFF, INPUT], gate_types))
    return len(nontrivial_gates)
