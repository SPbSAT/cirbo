# Boolean Circuit Tool


## Developer's environment

Python >=3.9 is used to cover all currently
[maintained versions](https://devguide.python.org/versions/).

1. Install `poetry` ([instruction](https://python-poetry.org/docs/)).
2. Setup virtual environment by running `poetry install`
3. Set your env to the oldest supported Python version `poetry env use 3.9`
4. Enable virtual environment using `poetry shell`
5. Init and update repository submodules `git submodule update --init --recursive`

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

## Formatters

`black`, `docformatter` and `usort` are available in poetry environment
and can be used to format code during development.

All of them can be run at once using:

`python ./tools/formatter.py`

## Tests

Tests are written and executed using `pytest`. 
To execute tests run `poetry run pytest`.

Tests are located at the `tests` subdirectory, and should be written for all
functionalities of the package. Also, directory structure of `tests` should
repeat structure of main `boolean-circuit-tool` package.

## CI flow

GitHub Actions are used for CI. Following checks are executed automatically for
each pull request and for each commit to the `main` branch.

Flow currently runs for `ubuntu` and `macos`, for python `3.9`.

CI checks include `pytest`, `mypy`, `flake8` for static code checks and `black`,
`docformatter` and `usort` are used to check if code is formatted properly.

Configuration of listed tools is located in `pyproject.toml`.
