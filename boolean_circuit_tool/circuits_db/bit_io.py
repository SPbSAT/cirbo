from boolean_circuit_tool.circuits_db.exceptions import BitIOError

__all__ = ['BitWriter', 'BitReader']


class BitWriter:
    def __init__(self):
        self._bytearray = bytearray()
        self._bit_pos = 8

    def __bytes__(self) -> bytes:
        return bytes(self._bytearray)

    def write(self, bit: bool) -> None:
        if self._bit_pos == 8:
            self._bytearray.append(0)
            self._bit_pos = 0
        self._bytearray[-1] |= bit << self._bit_pos
        self._bit_pos += 1

    def write_number(self, number: int, bit_length: int) -> None:
        if (number >> bit_length) != 0:
            raise BitIOError(
                f"Number {number} is too large to be encoded with {bit_length} bits"
            )
        for i in range(bit_length):
            self.write(bool((number >> i) & 1))

    def write_byte(self, byte_: int) -> None:
        self.write_number(byte_, 8)


class BitReader:
    def __init__(self, data: bytes):
        self._bytes = data
        self._byte_pos = 0
        self._bit_pos = 0

    def read(self) -> bool:
        if self._byte_pos >= len(self._bytes):
            raise BitIOError("No more bytes to read")

        current_byte = self._bytes[self._byte_pos]
        bit = (current_byte >> self._bit_pos) & 1

        self._bit_pos += 1
        if self._bit_pos == 8:
            self._bit_pos = 0
            self._byte_pos += 1

        return bool(bit)

    def read_number(self, bit_length: int) -> int:
        number = 0
        for i in range(bit_length):
            bit = self.read()
            number |= bit << i
        return number

    def read_byte(self) -> int:
        return self.read_number(8)
