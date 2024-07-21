import typing as tp
from pathlib import Path

from boolean_circuit_tool.circuits_db.exceptions import BinaryDictIOError

__all__ = ['read_binary_dict', 'write_binary_dict']

DICT_SIZE_BYTE_SIZE = 8
DICT_KEY_BYTE_SIZE = 2
DICT_VALUE_BYTE_SIZE = 2


def read_binary_dict(file_path: Path) -> tp.Dict[str, bytes]:
    data: tp.Dict[str, bytes] = dict()
    with file_path.open("rb") as stream:
        data_size = _read_unsigned_number(stream, DICT_SIZE_BYTE_SIZE)
        for i in range(data_size):
            key_len = _read_unsigned_number(stream, DICT_KEY_BYTE_SIZE)
            key = _read_exact_number_of_bytes(stream, key_len)
            key = key.decode(encoding='utf-8')
            val_len = _read_unsigned_number(stream, DICT_VALUE_BYTE_SIZE)
            val = _read_exact_number_of_bytes(stream, val_len)
            data[key] = val
    return data


def write_binary_dict(data: tp.Dict[str, bytes], file_path: Path) -> None:
    with file_path.open("wb") as stream:
        _write_unsigned_number(stream, len(data), DICT_KEY_BYTE_SIZE)
        for key, val in data.items():
            _write_unsigned_number(stream, len(key), DICT_KEY_BYTE_SIZE)
            stream.write(key.encode(encoding='utf-8'))
            _write_unsigned_number(stream, len(val), DICT_VALUE_BYTE_SIZE)
            stream.write(val)


def _read_unsigned_number(stream: tp.BinaryIO, byte_len: int) -> int:
    int_bytes = _read_exact_number_of_bytes(stream, byte_len)
    return int.from_bytes(int_bytes, byteorder="little", signed=False)


def _read_exact_number_of_bytes(stream: tp.BinaryIO, length: int) -> bytes:
    arr = stream.read(length)
    if len(arr) != length:
        # TODO: maybe create specific error for the IO operations?
        raise BinaryDictIOError("Unexpected EOF")
    return arr


def _expect_eof(stream: tp.BinaryIO) -> None:
    byte = stream.read(1)
    if byte:
        raise BinaryDictIOError("Expected end of file, but more data was found.")


def _write_unsigned_number(stream: tp.BinaryIO, number: int, byte_len: int) -> None:
    int_bytes = number.to_bytes(length=byte_len, byteorder="little", signed=False)
    stream.write(int_bytes)
