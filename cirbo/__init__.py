"""
Boolean Circuit Tool is a library designed to provide methods for easy boolean circuit
manipulations. Currently, it contains the following main subpackages:

1. ``cirbo.core`` -- core classes and abstractions, including ``Function`` protocol,
    its main implementations: ``TruthTable``, ``PyFunction`` and ``Circuit``, and a
    bunch of methods useful when working with boolean circuits.
2. ``cirbo.synthesis`` -- implementations of several method of boolean circuit
    synthesis. It defines plenty of methods for parametrized arithmetic circuit
    generation. Also, it contains ``CircuitFinderSat`` class, allowing search of
    boolean circuits which implement provided boolean function model, and several
    methods of circuit simplification (size reduction).
3. ``cirbo.sat`` -- utilities which allow to construct CNF, run SAT solvers, and
    also to convert Circuit SAT problem to SAT using Tseytin transformation and
    solve it using SAT solvers after.

"""

from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    pass
