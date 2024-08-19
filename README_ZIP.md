# Cirbo: A New Tool for Boolean Circuit Analysis and Synthesis

## Environment setup

Package `Python 3.9` is used to cover all currently [maintained Python versions](https://devguide.python.org/versions/).

Package was tested on `Ubuntu` and `Mac OS Ventura 13` machines.

1. Install following packages using your package manager:
   - dev version of `python3.9-dev` and `python3.9-distutils`
   - `build-essential` package for Ubuntu.
   - `cmake` and suitable C++ compiler, e.g. `gcc`
   - `graphviz` library

   Command for Ubuntu:
   ```shell
   sudo apt install python3-dev python3.9-dev python3.9-distutils gcc cmake graphviz build-essential
   ```
   
   > Note: python3.9 is unavailable in latest versions of Ubuntu, so `deadsnakes`
   > ppa may be useful: https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa

1. Install `poetry` ([official instruction](https://python-poetry.org/docs/)).
1. Build dist with extensions locally by running `poetry build`

   > Note: building `ABC` extension may take long time, one can skip it
   > using `(export DISABLE_ABC_CEXT=1 && poetry build && poetry install)`
   > command.

1. Setup virtual environment by running `poetry install`
1. Enable virtual environment using `poetry shell`

> Note: it may be necessary to restart an IDE after extensions
> are built and installed to refresh its index and stubs.

## Package structure

Some features of a package are demonstrated in the special modules located in
the `tutorial/` directory. The same code snippets are used in the paper's listings.
This is probably a first place that should be explored after environment is set up.

Directory `docs/` contains pre-rendered auto-api documentation of package `cirbo`.
Main classes and methods of `cirbo` can be explored it that documentation. To begin
exploration open `docs/index.html` in a browser.

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

Directory `data/` contains databases of small (nearly) optimal circuits, and
an exemplar of circuit encoded in BENCH format needed for `tutorial/`.

Directory `extensions/` contains C/C++ extensions written using `pybind11`.
Those extensions allow usage of `ABC` and `mockturtle` within python env.

Directory `third_party/` contains all third party libraries (excluding ones
installed form `pypi`) distributed alongside current zip archive (whilts
originally those dependencies are managed using `git submodule`). Those
include: `ABC`, `mockturtle` and `pybind11`.

Directory `tools/` contains utilities helpful for running linting checks or formatters.

Directory `tests/` contains all tests that cover both `cirbo/` and `extensions/`.

## Technical info

### C/C++ extensions

`cirbo` package provides integration with external `C/C++` libraries (`mockturtle`
and `ABC`). Such extensions are written using `pybind11` and should be built before
used locally. To build dependencies run `poetry build` and to install them  use
`poetry install` after.

> Note: to build dependencies one should have all building tools available
> in the system. Currently, dependencies require `C++` compiler and `cmake`
> to be available.

> Warning: `ABC` extension takes quite a long time (>10 min) to build. There is
> an option to avoid its building: `(export DISABLE_ABC_CEXT=1 && poetry build)`
> (parenthesis should be included). It can be helpful for fast testing because,
> but yet it may cause some `cirbo` functionality to not work property.

### Code quality

Code quality is sustained through both test-driven development and mandatory
linter checks.

#### Tests

Tests are written and executed using `pytest`. To execute unit tests run
`poetry run pytest`. Some tests have markers that disable their execution
by default due to their long execution times or extra dependencies requirements.
To  execute all tests run `poetry run pytest -m 'not manual'`.

#### Linters

`mypy` is used for static type checking and `flake8` is used for general linting.

`black`, `docformatter` and `usort` are used both to check if code is properly
formatted (e.g. in CI checks) and to format code locally.

#### Tools

All formatters can be run at once in poetry environment using following tool script:

`python ./tools/formatter.py`

All checks can be run at once in poetry environment using following tool script:

`python ./tools/check.py`

If everything is good, output is expected to be like the following:

```
(cirbo-py3.9) cirbo$ python ./tools/check.py
1. MYPY CHECK SUCCEED
2. FLAKE8 CHECK SUCCEED
3. PYTEST CHECK SUCCEED
4. USORT CHECK SUCCEED
5. DOCFORMATTER CHECK SUCCEED
6. BLACK CHECK SUCCEED
```
