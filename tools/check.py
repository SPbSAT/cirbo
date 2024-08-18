"""Module defines utility that runs CI checks locally."""

import argparse
import dataclasses
import operator
import subprocess
import sys
import textwrap


@dataclasses.dataclass(frozen=True)
class CheckReturn:
    """
    Carries return of one of checks.

    :attribute rc: return code of check. :attribute stdout: stdout of a check command.

    """

    rc: int
    stdout: str


def _call_command_with_buffer(command: str) -> CheckReturn:
    """
    :param command: shell command to execute.
    :return: tuple of two elements (return code, stdout+stderr buffer).

    """
    _prc = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return CheckReturn(rc=_prc.returncode, stdout=_prc.stdout.decode('utf-8'))


def _is_bad_rc(rc: int) -> bool:
    """Predicate that returns True iff `rc` is non-zero."""
    return rc != 0


def _check_project(*, short: bool):
    """
    Tool to run all CI required checks locally.

    Runs:
      1. mypy types checking.
      2. flake8 linting checks.
      3. pytest all cirbo tests.
      4. usort in check mode.
      5. docformatter in check mode.
      6. black in check mode.

    :param short: if set to False will print full output for failed checks,
           otherwise will trim output.

    """
    mypy_ret = _call_command_with_buffer("poetry run mypy -p cirbo")
    flake8_ret = _call_command_with_buffer("poetry run flake8 cirbo tests tools")
    pytest_ret = _call_command_with_buffer("poetry run pytest tests")
    usort_ret = _call_command_with_buffer("poetry run usort check cirbo/ tests/ tools/")
    docformatter_ret = _call_command_with_buffer(
        "poetry run docformatter --check --diff cirbo/ tests/ tools/"
    )
    black_ret = _call_command_with_buffer(
        "poetry run black --check --diff cirbo/ tests/ tools/"
    )

    all_ret = {
        'mypy': mypy_ret,
        'flake8': flake8_ret,
        'pytest': pytest_ret,
        'usort': usort_ret,
        'docformatter': docformatter_ret,
        'black': black_ret,
    }

    _wrapper = textwrap.TextWrapper(
        max_lines=10,
        width=100,
        break_long_words=False,
        replace_whitespace=False,
        placeholder='\n[...] To see full output run check.py without "-s" flag.',
    )
    for idx, (name, ret) in enumerate(all_ret.items(), start=1):
        if _is_bad_rc(ret.rc):
            print(f"{idx}. {name.upper()} CHECK FAILED\nstdout:", file=sys.stderr)
            if short:
                print(textwrap.indent(_wrapper.fill(ret.stdout), '* '), file=sys.stderr)
            else:
                print(textwrap.indent(ret.stdout, '* '), file=sys.stderr)
        else:
            print(f"{idx}. {name.upper()} CHECK SUCCEED", file=sys.stderr)

    _some_bad_rc = any(map(operator.attrgetter('rc'), all_ret.values()))
    if _some_bad_rc != 0:
        print(
            "CI check failed. Examine log for details and execute failed checks manually.",
            file=sys.stderr,
        )
    return _some_bad_rc


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--short', action='store_true')
    args = parser.parse_args()

    exit(_check_project(short=args.short))
