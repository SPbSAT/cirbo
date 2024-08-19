"""Module defines utility that formats project's code using "black", "docformatter" and
"usort"."""

import subprocess


def _format_project():
    usort_rc = subprocess.call(
        "poetry run usort format cirbo tests/ tools/ docs/", shell=True
    )
    docformatter_rc = subprocess.call(
        "poetry run docformatter --in-place cirbo/ tools/ tests/ docs/",
        shell=True,
    )
    black_rc = subprocess.call(
        "poetry run black cirbo/ tools/ tests/ docs/", shell=True
    )
    return any([usort_rc, docformatter_rc, black_rc])


if __name__ == '__main__':
    exit(_format_project())
