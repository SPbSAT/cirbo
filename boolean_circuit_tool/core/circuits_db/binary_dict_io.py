import typing as tp
from pathlib import Path

from boolean_circuit_tool.exceptions import BooleanCircuitToolError

__all__ = ['BinaryDictReader', 'BinaryDictWriter']

SIZE_LEN = 8
KEY_LEN = 2
VALUE_LEN = 2


class BinaryDictReader:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def read(self) -> tp.Dict[str, bytes]:
        data: tp.Dict[str, bytes] = dict()
        with self._file_path.open("rb") as stream:
            data_size = _read_unsigned_number(stream, SIZE_LEN)
            for i in range(data_size):
                key_len = _read_unsigned_number(stream, KEY_LEN)
                key = _read_exact_number_of_bytes(stream, key_len)
                key = key.decode(encoding='utf-8')
                val_len = _read_unsigned_number(stream, VALUE_LEN)
                val = _read_exact_number_of_bytes(stream, val_len)
                data[key] = val
        return data


class BinaryDictWriter:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def write(self, data: tp.Dict[str, bytes]) -> None:
        with self._file_path.open("wb") as stream:
            _write_unsigned_number(stream, len(data), KEY_LEN)
            for key, val in data.items():
                _write_unsigned_number(stream, len(key), KEY_LEN)
                stream.write(key.encode(encoding='utf-8'))
                _write_unsigned_number(stream, len(val), VALUE_LEN)
                stream.write(val)


def _read_unsigned_number(stream: tp.BinaryIO, byte_len: int) -> int:
    int_bytes = _read_exact_number_of_bytes(stream, byte_len)
    return int.from_bytes(int_bytes, byteorder="little", signed=False)


def _read_exact_number_of_bytes(stream: tp.BinaryIO, length: int) -> bytes:
    arr = stream.read(length)
    if len(arr) != length:
        # TODO: maybe create specific error for the IO operations?
        raise BooleanCircuitToolError("Unexpected EOF")
    return arr


def _expect_eof(stream: tp.BinaryIO) -> None:
    byte = stream.read(1)
    if byte:
        raise BooleanCircuitToolError("File is not ended while EOF expected")


def _write_unsigned_number(stream: tp.BinaryIO, number: int, byte_len: int) -> None:
    int_bytes = number.to_bytes(length=byte_len, byteorder="little", signed=False)
    stream.write(int_bytes)
