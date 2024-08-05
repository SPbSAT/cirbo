from io import BytesIO

import pytest
from boolean_circuit_tool.circuits_db.binary_dict_io import (
    _expect_eof,
    _read_exact_number_of_bytes,
    _read_unsigned_number,
    _write_unsigned_number,
    BinaryDictIOError,
    read_binary_dict,
    write_binary_dict,
)


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            {"key1": b"value1", "key2": b"value2"},
            b'\x00\x00\x00\x00\x00\x00\x00\x02'  # 2 keys, 8 bytes
            b'\x00\x04key1\x00\x06value1'  # key1 and value1
            b'\x00\x04key2\x00\x06value2',  # key2 and value2
        ),
        ({}, b'\x00\x00\x00\x00\x00\x00\x00\x00'),  # No keys, 8 bytes
        (
            {"k": b"v"},
            b'\x00\x00\x00\x00\x00\x00\x00\x01'  # 1 key, 8 bytes
            b'\x00\x01k\x00\x01v',  # key and value
        ),
    ],
)
def test_write_binary_dict(data, expected):
    stream = BytesIO()
    write_binary_dict(data, stream)
    stream.seek(0)
    result = stream.read()
    assert result == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        (
            b'\x00\x00\x00\x00\x00\x00\x00\x02'  # 2 keys, 8 bytes
            b'\x00\x04key1\x00\x06value1'  # key1 and value1
            b'\x00\x04key2\x00\x07val\x04ue2',  # key2 and value2
            {"key1": b"value1", "key2": b"val\x04ue2"},
        ),
        (b'\x00\x00\x00\x00\x00\x00\x00\x00', {}),  # No keys, 8 bytes
        (
            b'\x00\x00\x00\x00\x00\x00\x00\x01'  # 1 key, 8 bytes
            b'\x00\x01k\x00\x01v',  # key and value
            {"k": b"v"},
        ),
    ],
)
def test_read_binary_dict(data, expected):
    stream = BytesIO(data)
    result = read_binary_dict(stream)
    assert result == expected


def test_read_binary_dict_unexpected_eof():
    data = b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\x04key1\x00\x06val'
    stream = BytesIO(data)
    with pytest.raises(BinaryDictIOError, match="Unexpected EOF"):
        read_binary_dict(stream)


def test_expect_eof():
    data = b'\x00\x00\x00\x00\x00\x00\x00\x00extra'
    stream = BytesIO(data)
    with pytest.raises(
        BinaryDictIOError, match="Expected end of file, but more data was found."
    ):
        _expect_eof(stream)


@pytest.mark.parametrize(
    "data, byte_len, expected",
    [(b'\x00\x01', 2, 1), (b'\x00\xFF', 2, 255), (b'\x01\x00', 2, 256)],
)
def test_read_unsigned_number(data, byte_len, expected):
    stream = BytesIO(data)
    result = _read_unsigned_number(stream, byte_len)
    assert result == expected


@pytest.mark.parametrize(
    "number, byte_len, expected",
    [(1, 2, b'\x00\x01'), (255, 2, b'\x00\xFF'), (256, 2, b'\x01\x00')],
)
def test_write_unsigned_number(number, byte_len, expected):
    stream = BytesIO()
    _write_unsigned_number(stream, number, byte_len)
    result = stream.getvalue()
    assert result == expected


@pytest.mark.parametrize(
    "data, length, expected",
    [(b'\x01\x02\x03', 3, b'\x01\x02\x03'), (b'\x01\x02\x03\x04', 2, b'\x01\x02')],
)
def test_read_exact_number_of_bytes(data, length, expected):
    stream = BytesIO(data)
    result = _read_exact_number_of_bytes(stream, length)
    assert result == expected


def test_read_exact_number_of_bytes_eof():
    data = b'\x01\x02'
    stream = BytesIO(data)
    with pytest.raises(BinaryDictIOError, match="Unexpected EOF"):
        _read_exact_number_of_bytes(stream, 3)
