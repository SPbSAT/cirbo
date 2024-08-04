import pytest
from boolean_circuit_tool.circuits_db.bit_io import BitWriter, BitReader
from boolean_circuit_tool.circuits_db.exceptions import BitIOError


@pytest.mark.parametrize(
    "bits, expected_bytes",
    [
        ([True, False, True, False, True, False, True, False], b'\x55'),
        ([True, True, True, True, True, True, True, True], b'\xff'),
        ([False, False, False, False, False, False, False, False], b'\x00'),
        ([True, False], b'\x01'),
    ]
)
def test_bit_writer_write(bits, expected_bytes):
    writer = BitWriter()
    for bit in bits:
        writer.write(bit)
    assert bytes(writer) == expected_bytes


@pytest.mark.parametrize(
    "number, bit_length, expected_bytes",
    [
        (0, 3, b'\x00'),
        (1, 3, b'\x01'),
        (7, 3, b'\x07'),
        (255, 8, b'\xff'),
        (0b10101010, 8, b'\xaa'),
        (0b1100101, 7, b'\x65'),
    ]
)
def test_bit_writer_write_number(number, bit_length, expected_bytes):
    writer = BitWriter()
    writer.write_number(number, bit_length)
    assert bytes(writer) == expected_bytes


@pytest.mark.parametrize(
    "byte_, expected_bytes",
    [
        (0b11001100, b'\xcc'),
        (0b10101010, b'\xaa'),
        (0b11110000, b'\xf0'),
    ]
)
def test_bit_writer_write_byte(byte_, expected_bytes):
    writer = BitWriter()
    writer.write_byte(byte_)
    assert bytes(writer) == expected_bytes


def test_bit_writer_write_number_raises():
    writer = BitWriter()
    with pytest.raises(BitIOError, match="Number 256 is too large to be encoded with 8 bits"):
        writer.write_number(256, 8)


@pytest.mark.parametrize(
    "data, expected_bits",
    [
        (b'\x55', [True, False, True, False, True, False, True, False]),
        (b'\xff', [True, True, True, True, True, True, True, True]),
        (b'\x00', [False, False, False, False, False, False, False, False]),
        (b'\x01', [True, False]),
    ]
)
def test_bit_reader_read(data, expected_bits):
    reader = BitReader(data)
    for expected_bit in expected_bits:
        assert reader.read() is expected_bit


@pytest.mark.parametrize(
    "data, bit_length, expected_number",
    [
        (b'\x00', 3, 0),
        (b'\x01', 3, 1),
        (b'\x07', 3, 7),
        (b'\xff', 8, 255),
        (b'\xaa', 8, 0b10101010),
        (b'\x65', 7, 0b1100101),
    ]
)
def test_bit_reader_read_number(data, bit_length, expected_number):
    reader = BitReader(data)
    assert reader.read_number(bit_length) == expected_number


@pytest.mark.parametrize(
    "data, expected_byte",
    [
        (b'\xcc', 0b11001100),
        (b'\xaa', 0b10101010),
        (b'\xf0', 0b11110000),
    ]
)
def test_bit_reader_read_byte(data, expected_byte):
    reader = BitReader(data)
    assert reader.read_byte() == expected_byte


def test_bit_reader_read_raises():
    reader = BitReader(b'\x01')
    reader.read_byte()
    with pytest.raises(BitIOError, match="No more bytes to read"):
        reader.read()
