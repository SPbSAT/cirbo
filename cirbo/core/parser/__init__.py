"""Parser modules for circuit file formats."""

from cirbo.core.parser.aig import AIGParser
from cirbo.core.parser.bench import BenchToCircuit

__all__ = ['AIGParser', 'BenchToCircuit']
