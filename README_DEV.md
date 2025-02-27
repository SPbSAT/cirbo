# Cirbo: A New Tool for Boolean Circuit Analysis and Synthesis

## Environment setup

Package `Python 3.9` is used to cover all currently [maintained Python versions](https://devguide.python.org/versions/).

Package was tested on `Ubuntu` and `Mac OS Ventura 13` machines.

1. Update submodules `git submodule update --init --recursive`
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

1. Install `poetry` ([official instruction](https://python-poetry.org/docs/)) (`cirbo` requires `poetry` version to be `>= 2.0.0`)
1. Build dist with extensions locally by running `poetry build`

   > Note: building `ABC` extension may take long time, one can skip it
   > using `(export DISABLE_ABC_CEXT=1 && poetry build && poetry install)`
   > command.

1. Setup virtual environment by running `poetry install`
1. Execute `poetry env activate`
1. Enable virtual environment using command, which was printed by previous command. 

> Note: it may be necessary to restart an IDE after extensions
> are built and installed to refresh its index and stubs.
nstalled to refresh its index and stubs.

## Building extensions

This package provides bridges to some external `C/C++` libraries. Extensions
are written using `pybind11` and should be built before used locally. To build
dependencies run `poetry build` and to install them after use `poetry install`.

Note: to build dependencies one should have all building tools available
in the system. Currently, dependencies require `C++` compiler and `cmake`
to be available.

Some extensions can be disabled using environment variables if one doesn't
need them. For example `(export DISABLE_ABC_CEXT=1 && poetry build)` (parenthesis
should be included) will build wheels without `ABC` bridge module. It can be
helpful for CI or fast testing because `ABC` compilation times are heavy.

Tests that use `ABC` extension can be skipped by passing option `-m 'not ABC'`
to `pytest` run.

## Codestyle guidelines

One should follow simple rules:

1. For each public function unit tests should be written, covering:
   1. main usage cases.
   2. corner cases.
   3. wrong usage behaviour.
2. Type hints must be specified for all arguments and return values, as well
as for class attributes. Typehints for local variables are also welcome when
well-placed, but not obligatory.
3. All public Python objects (functions, classes, modules) must have docstrings.
For private and protected objects docstrings are encouraged but not obligatory.
4. All Python modules should include `__all__` definition, to avoid occasional
export of unwanted objects (e.g. export of imported objects).
5. Import of "all" objects (`from x import *`) must not be used.
6. All standard libraries should be imported as packages
(e.g. `import itertools`).
7. For package `typing` shortening `tp` should be used (`import typing as tp`).

## Checks

`mypy`, `flake8`, `pytest`, `black`, `docformatter` and `usort` are main checks
used in CI.

Those checks are available in poetry environment and can be invoked at once
locally using tool script:

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

shorten outputs mode can also be activated using flag `-s`:

`python ./tools/check.py -s`

## Formatters

`black`, `docformatter` and `usort` are available in poetry environment
and can be used to format code during development.

All of them can be run at once using tool script:

`python ./tools/formatter.py`

## Tests

Tests are written and executed using `pytest`.
To execute unit tests run `poetry run pytest`.
To execute all tests run `poetry run pytest -m 'not manual'`.

In addition to the standard tests, there are optional slow tests that interact with circuit databases. 
These tests require the corresponding database files. To execute these tests, use the following command:

```
poetry run pytest tests/ -m "db_xaig or db_aig" --db-xaig-path /path/to/xaig_db.bin --db-aig-path /path/to/aig_db.bin
```
Replace `/path/to/xaig_db.bin` and `/path/to/aig_db.bin` with the actual paths to your XAIG and AIG database files, respectively.

Tests are located at the `tests` subdirectory, and should be written for all
functionalities of the package. Also, directory structure of `tests` should
repeat structure of main `cirbo` package.

## Updating dependencies

To add or update python dependencies do the following:

1. Use `poetry add <package>` to add new dependency. To add dev-only dependency
use `poetry add <package> --group dev`. To update package version to the latest
of available execute `poetry update <package>`.
2. Commit changed `pyproject.toml` and `poetry.lock`.

If conflict occurred during merge request, one should repeat both steps above
on a fresh `main` version in order to correctly resolve valid versions for
all dependencies.

To bring new third-party dependency to the repository (e.g. some `C` library
sources) use `git submodule add <repository> third_party/<repository name>`.
Read more about submodules in
[docs](https://git-scm.com/book/en/v2/Git-Tools-Submodules).

## Writing extensions

`C/C++` extensions are written using `pybind11`. To create new extension one should:

1. Put source files to `extensions/<extension name>/src/`.
2. Add extension build specification to `CMakeLists.txt`.
3. Add extension module specification to `build.py`, to `ext_modules` variable.
4. Locally compile and install extensions
   ```sh
   poetry build
   poetry run
   ```
5. Add python tests to `tests/<extension name>` package.

## CI flow

GitHub Actions are used for CI. Following checks are executed automatically for
each pull request and for each commit to the `main` branch.

Flow currently runs for `ubuntu` and `macos`, for python `3.9`.

CI checks include `pytest`, `mypy`, `flake8` for static code checks and `black`,
`docformatter` and `usort` are used to check if code is formatted properly.

Configuration of listed tools is located in `pyproject.toml`.
