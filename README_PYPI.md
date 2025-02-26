# Cirbo: A New Tool for Boolean Circuit Analysis and Synthesis

Cirbo is a library for boolean circuit manipulations, providing methods to
analyse some given boolean circuits and synthetise new ones.

More info can be found at: https://github.com/SPbSAT/cirbo

## Package structure

Main `cirbo/` directory is a Python package root. It provides following subpackages:

- `core` &mdash; provides core classes and structures:
  - main boolean function abstractions: `Function` protocol to represent any
  boolean function and `FunctionModel` protocol to represent any partially
  defined boolean function
  - structures to carry representations of a boolean function (`TruthTable`,
  `PyFunction` and `Circuit`)
  - a `Circuit` class alongside with circuit manipulation operations.
- `synthesis` &mdash; provides tools for circuit synthesis:
  - methods to synthesize new circuit either by providing model of a function
  (e.g. truth table with don't care values) and then formulating and solving
  a SAT problem of finding feasible circuit.
  - methods to generate circuits describing arithmetical and logical operations
  (e.g. `generate_sum_n_bits` and `generate_if_then_else`) or add such gadget to
  an existing circuit.
- `minimization` &mdash; provides methods to minimize circuits:
  - low-effort circuit minimization algorithms (e.g. cleaning redundant gates,
  merging unary operators, merging duplicates, brute forcing equivalent gates).
  - high-effort circuit minimization trying to simplify small subcircuits within
  original circuit.
- `sat` &mdash; provides tools related to `SAT` solving:
  - method to build a miter from two given circuits.
  - method to reduce of `Circuit SAT` to `SAT` using Tseytin transformation.
  - method to call `SAT` solvers using [pysat toolkit](https://github.com/pysathq/pysat).
- `circuits_db` &mdash; provides methods to manage (read and write) database of
(nearly) optimal small circuits. Can be useful for either search for circuit with
given (partially defined) truth table or for an optimization of existing circuit.

> Note: most of a public methods provide docstrings, which can be useful when
> exploring `cirbo`.

