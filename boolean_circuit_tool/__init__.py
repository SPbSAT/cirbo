from importlib.metadata import PackageNotFoundError, version as _version

try:
    __version__ = _version(__name__)
except PackageNotFoundError:
    pass
