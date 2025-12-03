import os
import pathlib

import pytest

from cirbo.core.circuit.circuit import Circuit
from cirbo.core.circuit.gate import ALWAYS_FALSE, ALWAYS_TRUE, AND, IFF, INPUT, NOT
from cirbo.core.parser.aig import AIGParseError, AIGParser


def get_file_path(file_name: str) -> str:
    return str(
        pathlib.Path(os.path.dirname(__file__)).joinpath('./aigs/').joinpath(file_name)
    )


class TestAIGParserASCII:
    """Tests for ASCII AIG format (.aag)."""

    def test_constant_false(self):
        """Test parsing a circuit that outputs constant FALSE."""
        circuit = Circuit.from_aig_file(get_file_path('constant_false.aag'))

        assert circuit.output_size == 1
        # Output should be the constant FALSE gate
        output_label = circuit.outputs[0]
        assert circuit.get_gate(output_label).gate_type == ALWAYS_FALSE

    def test_constant_true(self):
        """Test parsing a circuit that outputs constant TRUE."""
        circuit = Circuit.from_aig_file(get_file_path('constant_true.aag'))

        assert circuit.output_size == 1
        # Output should be negation of FALSE (which is TRUE)
        output_label = circuit.outputs[0]
        output_gate = circuit.get_gate(output_label)
        # Either ALWAYS_TRUE or NOT of ALWAYS_FALSE
        assert output_gate.gate_type in (ALWAYS_TRUE, NOT)

    def test_buffer(self):
        """Test parsing a buffer circuit (output = input)."""
        circuit = Circuit.from_aig_file(get_file_path('buffer.aag'))

        assert circuit.input_size == 1
        assert circuit.output_size == 1

        # Output should be same as input (possibly through IFF gate)
        input_label = circuit.inputs[0]
        output_label = circuit.outputs[0]

        # Either the output is directly the input, or through an IFF gate
        if output_label != input_label:
            output_gate = circuit.get_gate(output_label)
            assert output_gate.gate_type == IFF
            assert input_label in output_gate.operands

        # Evaluate: output should equal input
        assert circuit.evaluate([False]) == [False]
        assert circuit.evaluate([True]) == [True]

    def test_inverter(self):
        """Test parsing an inverter circuit (output = NOT input)."""
        circuit = Circuit.from_aig_file(get_file_path('inverter.aag'))

        assert circuit.input_size == 1
        assert circuit.output_size == 1

        # Evaluate: output should be negation of input
        assert circuit.evaluate([False]) == [True]
        assert circuit.evaluate([True]) == [False]

    def test_and_gate(self):
        """Test parsing a simple AND gate circuit."""
        circuit = Circuit.from_aig_file(get_file_path('and_gate.aag'))

        assert circuit.input_size == 2
        assert circuit.output_size == 1

        # Evaluate AND gate truth table
        assert circuit.evaluate([False, False]) == [False]
        assert circuit.evaluate([False, True]) == [False]
        assert circuit.evaluate([True, False]) == [False]
        assert circuit.evaluate([True, True]) == [True]

    def test_or_gate(self):
        """Test parsing an OR gate circuit (implemented as NAND of negated inputs)."""
        circuit = Circuit.from_aig_file(get_file_path('or_gate.aag'))

        assert circuit.input_size == 2
        assert circuit.output_size == 1

        # Evaluate OR gate truth table: OR(a,b) = NOT(AND(NOT(a), NOT(b)))
        assert circuit.evaluate([False, False]) == [False]
        assert circuit.evaluate([False, True]) == [True]
        assert circuit.evaluate([True, False]) == [True]
        assert circuit.evaluate([True, True]) == [True]

    def test_half_adder(self):
        """Test parsing a half adder circuit with symbols."""
        circuit = Circuit.from_aig_file(get_file_path('half_adder.aag'))

        assert circuit.input_size == 2
        assert circuit.output_size == 2

        # Check that symbols were applied
        assert 'x' in circuit.inputs
        assert 'y' in circuit.inputs

        # Order inputs correctly
        circuit.order_inputs(['x', 'y'])

        results = [
            circuit.evaluate([False, False]),
            circuit.evaluate([False, True]),
            circuit.evaluate([True, False]),
            circuit.evaluate([True, True]),
        ]

        # Get output indices
        s_idx = circuit.index_of_output('s')
        c_idx = circuit.index_of_output('c')

        # Check XOR (sum) output
        assert results[0][s_idx] == False  # 0 XOR 0 = 0
        assert results[1][s_idx] == True  # 0 XOR 1 = 1
        assert results[2][s_idx] == True  # 1 XOR 0 = 1
        assert results[3][s_idx] == False  # 1 XOR 1 = 0

        # Check AND (carry) output
        assert results[0][c_idx] == False  # 0 AND 0 = 0
        assert results[1][c_idx] == False  # 0 AND 1 = 0
        assert results[2][c_idx] == False  # 1 AND 0 = 0
        assert results[3][c_idx] == True  # 1 AND 1 = 1


class TestAIGParserString:
    """Tests for parsing AIG from strings."""

    def test_parse_and_gate_from_string(self):
        """Test parsing AND gate from string."""
        aig_string = """aag 3 2 0 1 1
2
4
6
6 2 4
"""
        circuit = Circuit.from_aig_string(aig_string)

        assert circuit.input_size == 2
        assert circuit.output_size == 1

        # Evaluate AND gate
        assert circuit.evaluate([True, True]) == [True]
        assert circuit.evaluate([True, False]) == [False]

    def test_parse_inverter_from_string(self):
        """Test parsing inverter from string."""
        aig_string = """aag 1 1 0 1 0
2
3
"""
        circuit = Circuit.from_aig_string(aig_string)

        assert circuit.input_size == 1
        assert circuit.output_size == 1
        assert circuit.evaluate([False]) == [True]
        assert circuit.evaluate([True]) == [False]


class TestAIGParserErrors:
    """Tests for error handling in AIG parser."""

    def test_invalid_header(self):
        """Test that invalid header raises error."""
        with pytest.raises(AIGParseError):
            Circuit.from_aig_string("invalid header")

    def test_latches_not_supported(self):
        """Test that circuits with latches raise error."""
        # Circuit with 1 latch (L=1)
        aig_with_latch = """aag 1 0 1 1 0
2 3
2
"""
        with pytest.raises(AIGParseError, match="Latches are not supported"):
            Circuit.from_aig_string(aig_with_latch)

    def test_odd_input_literal(self):
        """Test that odd input literals raise error."""
        # Input literal must be even
        aig_odd_input = """aag 1 1 0 1 0
3
3
"""
        with pytest.raises(AIGParseError, match="Input literal must be even"):
            Circuit.from_aig_string(aig_odd_input)

    def test_odd_and_lhs(self):
        """Test that odd AND gate LHS raises error."""
        # AND gate LHS must be even
        aig_odd_and = """aag 3 2 0 1 1
2
4
7
7 2 4
"""
        with pytest.raises(AIGParseError, match="AND gate LHS must be even"):
            Circuit.from_aig_string(aig_odd_and)


class TestAIGParserDirect:
    """Direct tests for AIGParser class."""

    def test_parser_reuse(self):
        """Test that parser can be reused for multiple files."""
        parser = AIGParser()

        circuit1 = parser.parse_file(get_file_path('buffer.aag'))
        assert circuit1.input_size == 1

        circuit2 = parser.parse_file(get_file_path('and_gate.aag'))
        assert circuit2.input_size == 2

        # Circuits should be independent
        assert circuit1.input_size == 1

    def test_parse_bytes_ascii(self):
        """Test parsing ASCII format from bytes."""
        aig_bytes = b"""aag 1 1 0 1 0
2
3
"""
        parser = AIGParser()
        circuit = parser.parse_bytes(aig_bytes)

        assert circuit.input_size == 1
        assert circuit.evaluate([False]) == [True]
