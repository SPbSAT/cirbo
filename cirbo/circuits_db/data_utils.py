"""Module defines default paths to data files (e.g. databases)."""

import os
import pathlib
from importlib.abc import Traversable
from importlib.resources import files


__all__ = [
    'resolve_default_data_path',
    'DEFAULT_XAIG_DB_PATH',
    'DEFAULT_AIG_DB_PATH',
]


def resolve_default_data_path(data_path: os.PathLike[str]) -> pathlib.Path:
    """
    Resolves `Traversable` path to default data item (e.g. database of small circuits)
    based on given relative path to data file.

    :param data_path: relative to the `data/` directory path to the data file.

    """
    return pathlib.Path(files("cirbo").joinpath(f"data/{data_path}"))  # type: ignore


DEFAULT_XAIG_DB_PATH = resolve_default_data_path(pathlib.Path("xaig_db.bin.xz"))
DEFAULT_AIG_DB_PATH = resolve_default_data_path(pathlib.Path("aig_db.bin.xz"))
