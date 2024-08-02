# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['boolean_circuit_tool',
 'boolean_circuit_tool.core',
 'boolean_circuit_tool.core.circuit',
 'boolean_circuit_tool.core.parser',
 'boolean_circuit_tool.synthesis']

package_data = \
{'': ['*']}

install_requires = \
['click>=8.1.7,<9.0.0',
 'more-itertools>=10.3.0,<11.0.0',
 'pebble>=5.0.7,<6.0.0',
 'python-sat>=1.8.dev13,<2.0',
 'typing-extensions>=4.12.2,<5.0.0']

setup_kwargs = {
    'name': 'boolean-circuit-tool',
    'version': '0.1.0',
    'description': 'Tools and utilities for boolean circuit manipulations.',
    'long_description': '# Boolean Circuit Tool\n\n\n## Developer\'s environment\n\nPython >=3.9 is used to cover all currently\n[maintained versions](https://devguide.python.org/versions/).\n\n1. Install `poetry` ([instruction](https://python-poetry.org/docs/)).\n2. Setup virtual environment by running `poetry install`\n3. Set your env to the oldest supported Python version `poetry env use 3.9`\n4. Enable virtual environment using `poetry shell`\n5. Init and update repository submodules `git submodule update --init --recursive`\n\n## Building package\n\nSince package provides bridges to some external `C/C++` libraries, those\ndependencies should be built before local usage. To build dependencies\nrun `poetry build`\n\nNote: to build dependencies one should have all building tools available\nin the system. Currently, dependencies require `gcc` or `clang` compiler\nto be available.\n\n## Updating dependencies\n\nTo add or update python dependencies do the following:\n\n1. Use `poetry add <package>` to add new dependency. To add dev-only dependency\nuse `poetry add <package> --group dev`. To update package version to the latest\nof available execute `poetry update <package>`.\n2. Commit changed `pyproject.toml` and `poetry.lock`.\n\nIf conflict occurred during merge request, one should repeat both steps above\non a fresh `main` version in order to correctly resolve valid versions for\nall dependencies.\n\nTo bring new third-party dependency to the repository (e.g. some `C` library\nsources) use `git submodule add <repository> third_party/<repository name>`.\nRead more about submodules in\n[docs](https://git-scm.com/book/en/v2/Git-Tools-Submodules).\n\n## Codestyle guidelines\n\nOne should follow simple rules:\n\n1. For each public function unit tests should be written, covering:\n   1. main usage cases.\n   2. corner cases.\n   3. wrong usage behaviour.\n2. Type hints must be specified for all arguments and return values, as well\nas for class attributes. Typehints for local variables are also welcome when\nwell-placed, but not obligatory.\n3. All public Python objects (functions, classes, modules) must have docstrings.\nFor private and protected objects docstrings are encouraged but not obligatory.\n4. All Python modules should include `__all__` definition, to avoid occasional\nexport of unwanted objects (e.g. export of imported objects).\n5. Import of "all" objects (`from x import *`) must not be used.\n6. All standard libraries should be imported as packages\n(e.g. `import itertools`).\n7. For package `typing` shortening `tp` should be used (`import typing as tp`).\n\n## Formatters\n\n`black`, `docformatter` and `usort` are available in poetry environment\nand can be used to format code during development.\n\nAll of them can be run at once using:\n\n`python ./tools/formatter.py`\n\n## Tests\n\nTests are written and executed using `pytest`. \nTo execute tests run `poetry run pytest`.\n\nTests are located at the `tests` subdirectory, and should be written for all\nfunctionalities of the package. Also, directory structure of `tests` should\nrepeat structure of main `boolean-circuit-tool` package.\n\n## CI flow\n\nGitHub Actions are used for CI. Following checks are executed automatically for\neach pull request and for each commit to the `main` branch.\n\nFlow currently runs for `ubuntu` and `macos`, for python `3.9`.\n\nCI checks include `pytest`, `mypy`, `flake8` for static code checks and `black`,\n`docformatter` and `usort` are used to check if code is formatted properly.\n\nConfiguration of listed tools is located in `pyproject.toml`.\n',
    'author': 'Your Name',
    'author_email': 'you@example.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'None',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
