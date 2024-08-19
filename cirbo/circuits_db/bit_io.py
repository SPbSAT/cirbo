from cirbo.circuits_db.exceptions import BitIOError

__all__ = ['BitWriter', 'BitReader']


class BitWriter:
    """Class to write bits into a bytearray."""

    def __init__(self) -> None:
        self._bytearray = bytearray()
        self._bit_pos = 8

    def __bytes__(self) -> bytes:
        """
        Return the bytearray as bytes.

        :return: Byte representation of the written bits.

        """
        return bytes(self._bytearray)

    def write(self, bit: bool) -> None:
        """
        Write a single bit.

        :param bit: The bit to write (True for 1, False for 0).

        """
        if self._bit_pos == 8:
            self._bytearray.append(0)
            self._bit_pos = 0
        self._bytearray[-1] |= bit << self._bit_pos
        self._bit_pos += 1

    def write_number(self, number: int, bit_length: int) -> None:
        """
        Write a number using a specified bit length.

        :param number: The number to write.
        :param bit_length: The number of bits to use for the number.
        :raises BitIOError: If the number is too large to fit in the specified bit
            length.

        """
        if (number >> bit_length) != 0:
            raise BitIOError(
                f"Number {number} is too large to be encoded with {bit_length} bits"
            )
        for i in range(bit_length):
            self.write(bool((number >> i) & 1))

    def write_byte(self, byte_: int) -> None:
        """
        Write a single byte.

        :param byte_: The byte to write.

        """
        self.write_number(byte_, 8)


class BitReader:
    """Class to read bits from a bytearray."""

    def __init__(self, data: bytes) -> None:
        self._bytes = data
        self._byte_pos = 0
        self._bit_pos = 0

    def read(self) -> bool:
        """
        Read a single bit.

        :return: The read bit (True for 1, False for 0).
        :raises BitIOError: If there are no more bytes to read.

        """
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
        """
        Read a number using a specified bit length.

        :param bit_length: The number of bits to read for the number.
        :return: The read number.

        """
        number = 0
        for i in range(bit_length):
            bit = self.read()
            number |= bit << i
        return number

    def read_byte(self) -> int:
        """
        Read a single byte.

        :return: The read byte.

        """
        return self.read_number(8)
