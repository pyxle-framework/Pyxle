"""Pyxle framework package metadata and public API surface."""

from importlib.metadata import PackageNotFoundError, version

from .runtime import server

try:
    __version__ = version("pyxle-framework")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["__version__", "server"]
