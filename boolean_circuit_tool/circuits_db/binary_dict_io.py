import typing as tp

from boolean_circuit_tool.circuits_db.exceptions import BinaryDictIOError

__all__ = ['read_binary_dict', 'write_binary_dict']

# Number of bytes used to store the size of the dictionary
DICT_SIZE_BYTE_SIZE = 8

# Number of bytes used to store the length of a dictionary key
DICT_KEY_BYTE_SIZE = 2

# Number of bytes used to store the length of a dictionary value
DICT_VALUE_BYTE_SIZE = 2


def read_binary_dict(stream: tp.BinaryIO) -> tp.Dict[str, bytes]:
    """
    Read a dictionary from a binary stream.

    The dictionary keys are strings and the values are bytes.

    :param stream: A binary stream to read the dictionary from.
    :return: A dictionary with string keys and byte values.

    """
    data: tp.Dict[str, bytes] = dict()
    data_size = _read_unsigned_number(stream, DICT_SIZE_BYTE_SIZE)
    for i in range(data_size):
        key_len = _read_unsigned_number(stream, DICT_KEY_BYTE_SIZE)
        key_bytes = _read_exact_number_of_bytes(stream, key_len)
        key = key_bytes.decode(encoding='utf-8')
        val_len = _read_unsigned_number(stream, DICT_VALUE_BYTE_SIZE)
        val = _read_exact_number_of_bytes(stream, val_len)
        data[key] = val
    _expect_eof(stream)
    return data


def write_binary_dict(data: tp.Dict[str, bytes], stream: tp.BinaryIO) -> None:
    """
    Write a dictionary to a binary stream.

    The dictionary keys are strings and the values are bytes.

    :param data: The dictionary to write.
    :param stream: The binary stream to write the dictionary to.

    """
    _write_unsigned_number(stream, len(data), DICT_SIZE_BYTE_SIZE)
    for key, val in data.items():
        _write_unsigned_number(stream, len(key), DICT_KEY_BYTE_SIZE)
        stream.write(key.encode(encoding='utf-8'))
        _write_unsigned_number(stream, len(val), DICT_VALUE_BYTE_SIZE)
        stream.write(val)


def _read_unsigned_number(stream: tp.BinaryIO, byte_len: int) -> int:
    int_bytes = _read_exact_number_of_bytes(stream, byte_len)
    return int.from_bytes(int_bytes, byteorder="big", signed=False)


def _write_unsigned_number(stream: tp.BinaryIO, number: int, byte_len: int) -> None:
    int_bytes = number.to_bytes(length=byte_len, byteorder="big", signed=False)
    stream.write(int_bytes)


def _read_exact_number_of_bytes(stream: tp.BinaryIO, length: int) -> bytes:
    arr = stream.read(length)
    if len(arr) != length:
        raise BinaryDictIOError("Unexpected EOF")
    return arr


def _expect_eof(stream: tp.BinaryIO) -> None:
    byte = stream.read(1)
    if byte:
        raise BinaryDictIOError("Expected end of file, but more data was found.")
