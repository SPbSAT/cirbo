# Cirbo: A New Tool for Boolean Circuit Analysis and Synthesis

Cirbo is a Python library that provides methods for
Boolean circuit manipulation, analysis, and synthesis

Usage example
```py
from cirbo.core import Circuit, Gate, gate
from cirbo.synthesis.generation.arithmetics import add_sum_n_bits

# Create an empty circuit with 6 inputs.
ckt = Circuit.bare_circuit(input_size=6)
# Generate and connect a "gadget" subcircuit
# that computes the sum of the input bits.
b0, b1, b2 = add_sum_n_bits(ckt, ckt.inputs)
# Manually add output gate that yield True only
# if at least half of the inputs are True.
ckt.add_gate(Gate('a0', gate.AND, (b0, b1)))
ckt.add_gate(Gate('a1', gate.OR, ('a0', b2)))
ckt.mark_as_output('a1')

# Calculate general boolean function properties.
print(f"Is monotone: {ckt.is_monotone()}")
print(f"Is symmetric: {ckt.is_symmetric()}")
print(f"Is constant: {ckt.is_constant()}")

# Draw the graph and show the image in the default viewer.
ckt.view_graph()
```

More examples are available in the [tutorial](https://github.com/SPbSAT/cirbo/tree/main/tutorial).

## Installation

The package is currently available on Test PyPI and will be published on PyPI after testing.

To install the package from Test PyPI into your virtual environment, run:

```sh
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ cirbo
```

Instructions on how to set up the development environment are provided in the separate [dev README](README_DEV.md).

## Documentation

The main library features are described in the paper "Cirbo: A New Tool for Boolean Circuit Analysis and Synthesis" ([arXiv](https://arxiv.org/abs/2412.14933), [AAAI-25](https://ojs.aaai.org/index.php/AAAI/article/view/33207)).

Currently, `cirbo` does not have web-hosted documentation, but it can be built locally using Sphinx (see the [dev README](README_DEV.md) for details).

## Package structure

Some features of the package are demonstrated in the example modules located in
the `tutorial/` directory. Similar code snippets are used in the paper's listings.
This is probably the first place to explore after environment is set up.

The `cirbo/` directory is the root of the Python package and contains the following subpackages:

- `core` &mdash; provides core classes and structures:
  - core abstractions for Boolean functions: the `Function` protocol to represent any
  Boolean function and the `FunctionModel` protocol to represent partially
  defined Boolean functions.
  - data structures for representing Boolean functions (`TruthTable`,
  `PyFunction` and `Circuit`)
  - the `Circuit` class along with circuit manipulation operations.
- `synthesis` &mdash; provides tools for circuit synthesis:
  - methods to synthesize new circuit either by providing model of a function
  (e.g. truth table with don't care values) and then formulating and solving
  a SAT problem of finding feasible circuit.
  - methods to generate circuits describing arithmetic and logical operations
  (e.g. `generate_sum_n_bits` and `generate_if_then_else`) or to add such gadgets to
  an existing circuit.
- `minimization` &mdash; provides methods to minimize circuits:
  - lightweight circuit minimization algorithms (e.g. cleaning redundant gates,
  merging unary operators, merging duplicates, brute-force search for equivalent gates).
  - heavyweight circuit minimization that tries to simplify small subcircuits within
  original circuit.
- `sat` &mdash; provides tools related to SAT solving:
  - a method to build a miter from two given circuits.
  - a method to reduce of circuit satisfiability to SAT using Tseytin transformation.
  - a method to call SAT solvers using [pysat toolkit](https://github.com/pysathq/pysat).
- `circuits_db` &mdash; provides methods to manage (read and write) database of
(nearly) optimal small circuits. It can be useful for searching for a circuit with
a given (partially defined) truth table or for optimizing an existing circuit.

> Note: most public methods have docstrings, which are useful when exploring `cirbo`.

## Technical info

### C/C++ extensions

The `cirbo` package provides integration with external C/C++ libraries (`mockturtle` and `ABC`).
These extensions are written using `pybind11` and should be built before being used locally.
To build the dependencies, run `poetry build`, and then install the package with `poetry install`.

> Note: to build the dependencies, you need the required build tools installed
> on your system. Currently, the dependencies require a C++ compiler and CMake.

> Warning: the `ABC` extension takes quite a long time (>10 min) to build. You
> can skip building it with `(export DISABLE_ABC_CEXT=1 && poetry build)` (parentheses
> should be included). This can be helpful for faster testing, but it may cause
> some `cirbo` functionality to not work properly.
