"""
Subpackage contains methods that help store, read and work with database of (nearly)
optimal small circuits.

Can be useful for either search for circuit with given (partially defined) truth table
or for an optimization of existing circuit.

"""

from .db import CircuitsDatabase

__all__ = [
    'CircuitsDatabase',
]
