"""
Implementation of AIG (And-Inverter Graph) format parsing.

Supports both ASCII (.aag) and binary (.aig) AIGER formats.
See: http://fmv.jku.at/aiger/ for format specification.

Note: This implementation only supports combinational circuits (L=0, no latches).

"""

import io
import logging
import pathlib
import typing as tp

from cirbo.core.circuit import gate
from cirbo.core.circuit.circuit import Circuit


logger = logging.getLogger(__name__)

__all__ = ['AIGParser']


class AIGParseError(Exception):
    """Error during AIG file parsing."""

    pass


class AIGParser:
    """
    Parser for AIGER format files (both ASCII .aag and binary .aig).

    The AIGER format represents circuits as And-Inverter Graphs (AIGs). This parser
    converts AIG files to Circuit objects.

    Only combinational circuits (without latches) are supported.

    """

    def __init__(self):
        self._circuit: Circuit = Circuit()
        self._literal_to_label: dict[int, gate.Label] = {}
        self._symbols: dict[str, dict[int, str]] = {'i': {}, 'o': {}, 'l': {}}

    def parse_file(self, file_path: str) -> Circuit:
        """
        Parse an AIG file and return a Circuit.

        :param file_path: path to the .aag or .aig file.
        :return: parsed Circuit object.

        """
        path = pathlib.Path(file_path)
        if path.suffix == '.aag':
            with path.open('r') as f:
                return self._parse_ascii(f)
        elif path.suffix == '.aig':
            with path.open('rb') as f:
                return self._parse_binary(f)
        else:
            # Try to detect format from header
            with path.open('rb') as f:
                header_start = f.read(3)
                f.seek(0)
                if header_start == b'aag':
                    # Re-open as text
                    pass
                elif header_start == b'aig':
                    return self._parse_binary(f)
                else:
                    raise AIGParseError(
                        f"Unknown file format. Header starts with: {header_start!r}"
                    )
            with path.open('r') as f:
                return self._parse_ascii(f)

    def parse_string(self, content: str) -> Circuit:
        """
        Parse an AIG string (ASCII format only) and return a Circuit.

        :param content: string containing AIG data in ASCII format.
        :return: parsed Circuit object.

        """
        with io.StringIO(content) as f:
            return self._parse_ascii(f)

    def parse_bytes(self, content: bytes) -> Circuit:
        """
        Parse AIG bytes (can be ASCII or binary format) and return a Circuit.

        :param content: bytes containing AIG data.
        :return: parsed Circuit object.

        """
        if content.startswith(b'aag'):
            return self.parse_string(content.decode('ascii'))
        elif content.startswith(b'aig'):
            with io.BytesIO(content) as f:
                return self._parse_binary(f)
        else:
            raise AIGParseError("Unknown format. Must start with 'aag' or 'aig'.")

    def _parse_ascii(self, stream: tp.TextIO) -> Circuit:
        """Parse ASCII AIG format (.aag)."""
        self._circuit = Circuit()
        self._literal_to_label = {}
        self._symbols = {'i': {}, 'o': {}, 'l': {}}

        # Parse header
        header_line = stream.readline().strip()
        header_parts = header_line.split()

        if len(header_parts) < 6 or header_parts[0] != 'aag':
            raise AIGParseError(f"Invalid AAG header: {header_line}")

        m, i, l, o, a = map(int, header_parts[1:6])
        logger.debug(f"AAG header: M={m}, I={i}, L={l}, O={o}, A={a}")

        if l != 0:
            raise AIGParseError(
                "Latches are not supported. Only combinational circuits (L=0) allowed."
            )

        # Register constants
        self._literal_to_label[0] = self._get_or_create_false()
        self._literal_to_label[1] = self._get_or_create_true()

        # Parse inputs
        input_literals: list[int] = []
        for idx in range(i):
            line = stream.readline().strip()
            if not line:
                raise AIGParseError(f"Expected input literal at line {idx + 2}")
            lit = int(line)
            if lit % 2 != 0:
                raise AIGParseError(f"Input literal must be even, got {lit}")
            input_literals.append(lit)
            label = f"i{idx}"
            self._circuit._emplace_gate(label, gate.INPUT)
            self._literal_to_label[lit] = label
            logger.debug(f"Input {idx}: literal={lit}, label={label}")

        # Parse outputs (just collect literals for now)
        output_literals: list[int] = []
        for idx in range(o):
            line = stream.readline().strip()
            if not line:
                raise AIGParseError(f"Expected output literal at line {i + idx + 2}")
            output_literals.append(int(line))
            logger.debug(f"Output {idx}: literal={output_literals[-1]}")

        # Parse AND gates - first collect all definitions
        # (ASCII format allows arbitrary order, so we need two passes)
        and_gates: list[tuple[int, int, int]] = []
        for idx in range(a):
            line = stream.readline().strip()
            if not line:
                raise AIGParseError(f"Expected AND gate at line {i + o + idx + 2}")
            parts = line.split()
            if len(parts) != 3:
                raise AIGParseError(f"Invalid AND gate definition: {line}")
            lhs, rhs0, rhs1 = map(int, parts)
            if lhs % 2 != 0:
                raise AIGParseError(f"AND gate LHS must be even, got {lhs}")
            and_gates.append((lhs, rhs0, rhs1))
            # Pre-register the LHS literal (gate will be created later)
            and_label = f"n{lhs // 2}"
            self._literal_to_label[lhs] = and_label

        # Now create AND gates in topological order
        self._create_and_gates_topological(and_gates)

        # Parse optional symbol table and comments
        for line in stream:
            line = line.strip()
            if not line:
                continue
            if line.startswith('c'):
                # Comment section starts, stop parsing
                break
            if line[0] in 'ilo' and len(line) > 1:
                # Symbol definition
                self._parse_symbol(line)

        # Apply symbols and set up circuit
        self._apply_symbols(input_literals, output_literals)
        self._set_outputs(output_literals)

        return self._circuit

    def _create_and_gates_topological(
        self, and_gates: list[tuple[int, int, int]]
    ) -> None:
        """Create AND gates in topological order to handle forward references."""
        # Build dependency graph
        lhs_set = {lhs for lhs, _, _ in and_gates}
        gate_map = {lhs: (rhs0, rhs1) for lhs, rhs0, rhs1 in and_gates}
        created: set[int] = set()

        def get_base_literal(lit: int) -> int:
            """Get the base (even) literal for any literal."""
            return lit & ~1  # Clear the LSB

        def create_gate(lhs: int) -> None:
            """Recursively create a gate and its dependencies."""
            if lhs in created:
                return

            rhs0, rhs1 = gate_map[lhs]

            # Create dependencies first
            base0 = get_base_literal(rhs0)
            base1 = get_base_literal(rhs1)

            if base0 in lhs_set and base0 not in created:
                create_gate(base0)
            if base1 in lhs_set and base1 not in created:
                create_gate(base1)

            # Now create this gate
            self._add_and_gate_internal(lhs, rhs0, rhs1)
            created.add(lhs)

        # Create all gates
        for lhs, _, _ in and_gates:
            create_gate(lhs)

    def _parse_binary(self, stream: tp.BinaryIO) -> Circuit:
        """Parse binary AIG format (.aig)."""
        self._circuit = Circuit()
        self._literal_to_label = {}
        self._symbols = {'i': {}, 'o': {}, 'l': {}}

        # Parse header (ASCII part)
        header_line = b''
        while True:
            ch = stream.read(1)
            if ch == b'\n':
                break
            if not ch:
                raise AIGParseError("Unexpected EOF while reading header")
            header_line += ch

        header_str = header_line.decode('ascii').strip()
        header_parts = header_str.split()

        if len(header_parts) < 6 or header_parts[0] != 'aig':
            raise AIGParseError(f"Invalid AIG header: {header_str}")

        m, i, l, o, a = map(int, header_parts[1:6])
        logger.debug(f"AIG header: M={m}, I={i}, L={l}, O={o}, A={a}")

        if l != 0:
            raise AIGParseError(
                "Latches are not supported. Only combinational circuits (L=0) allowed."
            )

        # Register constants
        self._literal_to_label[0] = self._get_or_create_false()
        self._literal_to_label[1] = self._get_or_create_true()

        # In binary format, inputs are implicit: literals 2, 4, ..., 2*I
        input_literals: list[int] = []
        for idx in range(i):
            lit = 2 * (idx + 1)
            input_literals.append(lit)
            label = f"i{idx}"
            self._circuit._emplace_gate(label, gate.INPUT)
            self._literal_to_label[lit] = label
            logger.debug(f"Input {idx}: literal={lit}, label={label}")

        # Parse output literals (ASCII, one per line)
        output_literals: list[int] = []
        for idx in range(o):
            line = b''
            while True:
                ch = stream.read(1)
                if ch == b'\n':
                    break
                if not ch:
                    raise AIGParseError("Unexpected EOF while reading outputs")
                line += ch
            output_literals.append(int(line.decode('ascii').strip()))
            logger.debug(f"Output {idx}: literal={output_literals[-1]}")

        # Parse AND gates in binary delta encoding
        # AND variable indices are: I+L+1, I+L+2, ..., I+L+A (= M)
        # AND literals are: 2*(I+L)+2, 2*(I+L)+4, ..., 2*M
        for idx in range(a):
            lhs = 2 * (i + l + idx + 1)
            delta0 = self._decode_binary_number(stream)
            delta1 = self._decode_binary_number(stream)
            rhs0 = lhs - delta0
            rhs1 = rhs0 - delta1
            self._add_and_gate(lhs, rhs0, rhs1)

        # Try to parse optional symbol table (ASCII section after binary data)
        try:
            remaining = stream.read()
            if remaining:
                text_part = remaining.decode('ascii', errors='ignore')
                for text_line in text_part.split('\n'):
                    text_line = text_line.strip()
                    if not text_line:
                        continue
                    if text_line.startswith('c'):
                        break
                    if text_line[0] in 'ilo' and len(text_line) > 1:
                        self._parse_symbol(text_line)
        except Exception:
            # Symbol parsing is optional, ignore errors
            pass

        # Apply symbols and set up circuit
        self._apply_symbols(input_literals, output_literals)
        self._set_outputs(output_literals)

        return self._circuit

    def _decode_binary_number(self, stream: tp.BinaryIO) -> int:
        """
        Decode a binary-encoded unsigned integer from the stream.

        Uses AIGER's variable-length encoding where the MSB of each byte indicates if
        more bytes follow.

        """
        result = 0
        shift = 0
        while True:
            byte_data = stream.read(1)
            if not byte_data:
                raise AIGParseError("Unexpected EOF while decoding binary number")
            byte = byte_data[0]
            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
        return result

    def _add_and_gate(self, lhs: int, rhs0: int, rhs1: int) -> None:
        """
        Add an AND gate to the circuit (for binary format where order is guaranteed).

        :param lhs: left-hand side literal (output of AND gate, must be even).
        :param rhs0: first right-hand side literal (first input).
        :param rhs1: second right-hand side literal (second input).

        """
        if lhs % 2 != 0:
            raise AIGParseError(f"AND gate LHS must be even, got {lhs}")

        # Pre-register the LHS literal
        and_label = f"n{lhs // 2}"
        self._literal_to_label[lhs] = and_label

        self._add_and_gate_internal(lhs, rhs0, rhs1)

    def _add_and_gate_internal(self, lhs: int, rhs0: int, rhs1: int) -> None:
        """
        Internal method to add an AND gate (LHS already registered).

        :param lhs: left-hand side literal (output of AND gate).
        :param rhs0: first right-hand side literal (first input).
        :param rhs1: second right-hand side literal (second input).

        """
        logger.debug(f"AND gate: {lhs} = {rhs0} & {rhs1}")

        # Get or create labels for operands
        op0_label = self._get_literal_label(rhs0)
        op1_label = self._get_literal_label(rhs1)

        # Create the AND gate
        and_label = self._literal_to_label[lhs]
        self._circuit._emplace_gate(and_label, gate.AND, (op0_label, op1_label))

    def _get_literal_label(self, literal: int) -> gate.Label:
        """
        Get the label for a literal, creating NOT gates as needed for negated literals.

        :param literal: the literal to get label for.
        :return: label of the gate representing this literal.

        """
        # Check if we already have this literal
        if literal in self._literal_to_label:
            return self._literal_to_label[literal]

        # For negated literals (odd), create a NOT gate
        if literal % 2 == 1:
            base_literal = literal - 1
            if base_literal not in self._literal_to_label:
                raise AIGParseError(
                    f"Base literal {base_literal} not defined for negated literal {literal}"
                )
            base_label = self._literal_to_label[base_literal]
            not_label = f"not_{base_label}"

            # Check if NOT gate already exists
            if not_label not in self._circuit.gates:
                self._circuit._emplace_gate(not_label, gate.NOT, (base_label,))

            self._literal_to_label[literal] = not_label
            return not_label

        raise AIGParseError(f"Undefined literal: {literal}")

    def _get_or_create_false(self) -> gate.Label:
        """Get or create an ALWAYS_FALSE gate."""
        label = "__false__"
        if label not in self._circuit.gates:
            self._circuit._emplace_gate(label, gate.ALWAYS_FALSE)
        return label

    def _get_or_create_true(self) -> gate.Label:
        """Get or create an ALWAYS_TRUE gate."""
        label = "__true__"
        if label not in self._circuit.gates:
            self._circuit._emplace_gate(label, gate.ALWAYS_TRUE)
        return label

    def _parse_symbol(self, line: str) -> None:
        """Parse a symbol table entry."""
        if len(line) < 2:
            return

        sym_type = line[0]
        rest = line[1:]

        # Find the position number
        space_idx = rest.find(' ')
        if space_idx == -1:
            return

        try:
            pos = int(rest[:space_idx])
            name = rest[space_idx + 1 :]
            self._symbols[sym_type][pos] = name
            logger.debug(f"Symbol: {sym_type}{pos} = {name}")
        except ValueError:
            pass

    def _apply_symbols(
        self, input_literals: list[int], output_literals: list[int]
    ) -> None:
        """Apply symbol names to inputs by renaming gates."""
        # Rename inputs if symbols are provided
        for idx, lit in enumerate(input_literals):
            if idx in self._symbols['i']:
                old_label = self._literal_to_label[lit]
                new_label = self._symbols['i'][idx]
                if old_label != new_label and old_label in self._circuit.gates:
                    self._rename_gate_in_parser(old_label, new_label, lit)

    def _rename_gate_in_parser(
        self, old_label: gate.Label, new_label: gate.Label, literal: int
    ) -> None:
        """Rename a gate during parsing, updating all references."""
        if new_label in self._circuit.gates:
            # Name conflict, keep original
            return

        # Get the gate
        old_gate = self._circuit.gates[old_label]

        # First, handle any NOT gates that reference this gate
        old_not_label = f"not_{old_label}"
        new_not_label = f"not_{new_label}"
        if old_not_label in self._circuit.gates:
            # Remove old NOT gate
            del self._circuit._gates[old_not_label]
            if old_not_label in self._circuit._gate_to_users:
                del self._circuit._gate_to_users[old_not_label]

            # Update literal_to_label for the NOT gate
            for lit, label in list(self._literal_to_label.items()):
                if label == old_not_label:
                    self._literal_to_label[lit] = new_not_label

            # Will be recreated after the main gate is renamed

        # Remove old gate
        del self._circuit._gates[old_label]
        if old_label in self._circuit._inputs:
            self._circuit._inputs.remove(old_label)
        if old_label in self._circuit._gate_to_users:
            del self._circuit._gate_to_users[old_label]

        # Add with new label
        self._circuit._emplace_gate(new_label, old_gate.gate_type, old_gate.operands)
        self._literal_to_label[literal] = new_label

        # Now recreate NOT gate with new name if it existed
        if old_not_label in [f"not_{old_label}"]:
            # Check if we need to recreate it
            for lit, label in list(self._literal_to_label.items()):
                if label == new_not_label and new_not_label not in self._circuit.gates:
                    self._circuit._emplace_gate(new_not_label, gate.NOT, (new_label,))
                    break

        # Update any gates that reference the old label or old NOT label
        for gate_label, g in list(self._circuit._gates.items()):
            needs_update = False
            new_operands = []
            for op in g.operands:
                if op == old_label:
                    new_operands.append(new_label)
                    needs_update = True
                elif op == old_not_label:
                    new_operands.append(new_not_label)
                    needs_update = True
                else:
                    new_operands.append(op)
            if needs_update:
                # Need to rebuild gate and update users
                self._circuit._gates[gate_label] = gate.Gate(
                    gate_label, g.gate_type, tuple(new_operands)
                )
                # Update user tracking
                if new_label in new_operands:
                    if new_label not in self._circuit._gate_to_users:
                        self._circuit._gate_to_users[new_label] = []
                    if gate_label not in self._circuit._gate_to_users[new_label]:
                        self._circuit._gate_to_users[new_label].append(gate_label)
                if new_not_label in new_operands:
                    if new_not_label not in self._circuit._gate_to_users:
                        self._circuit._gate_to_users[new_not_label] = []
                    if gate_label not in self._circuit._gate_to_users[new_not_label]:
                        self._circuit._gate_to_users[new_not_label].append(gate_label)

    def _set_outputs(self, output_literals: list[int]) -> None:
        """Set the circuit outputs based on output literals."""
        output_labels: list[gate.Label] = []
        for idx, lit in enumerate(output_literals):
            label = self._get_literal_label(lit)
            # Use symbol name for output if available
            if idx in self._symbols['o']:
                output_name = self._symbols['o'][idx]
                # Create an IFF gate to give the output a proper name
                if output_name not in self._circuit.gates:
                    self._circuit._emplace_gate(output_name, gate.IFF, (label,))
                    label = output_name
            output_labels.append(label)

        self._circuit.set_outputs(output_labels)
