"""Error boundary resolution for ``error.pyx`` and ``not-found.pyx`` pages.

Pyxle supports file-convention error pages inspired by Next.js:

* ``pages/error.pyx``               — root error boundary
* ``pages/dashboard/error.pyx``     — catches errors within ``/dashboard/*``
* ``pages/not-found.pyx``           — root 404 page
* ``pages/dashboard/not-found.pyx`` — catches 404s within ``/dashboard/*``

Error boundaries are resolved by walking **up** the directory tree from the
failing route until a matching error/not-found page is found. The closest
ancestor wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Optional, Sequence


_ERROR_FILENAMES = frozenset({"error.pyx"})
_NOT_FOUND_FILENAMES = frozenset({"not-found.pyx"})
_BOUNDARY_FILENAMES = _ERROR_FILENAMES | _NOT_FOUND_FILENAMES


def is_error_boundary_file(relative_path_posix: str) -> bool:
    """Return True if the source file is an error or not-found page."""
    name = PurePosixPath(relative_path_posix).name.lower()
    return name in _BOUNDARY_FILENAMES


def is_error_page(relative_path_posix: str) -> bool:
    """Return True if the source file is an ``error.pyx``."""
    return PurePosixPath(relative_path_posix).name.lower() in _ERROR_FILENAMES


def is_not_found_page(relative_path_posix: str) -> bool:
    """Return True if the source file is a ``not-found.pyx``."""
    return PurePosixPath(relative_path_posix).name.lower() in _NOT_FOUND_FILENAMES


@dataclass(frozen=True, slots=True)
class ErrorBoundaryRegistry:
    """Maps directory segments to their compiled error / not-found page routes.

    Keys are directory paths relative to ``pages/`` in POSIX form. The root
    directory is represented as ``"."``.

    Example::

        error_pages = {".": <root error.pyx route>, "dashboard": <dashboard error.pyx route>}
        not_found_pages = {".": <root not-found.pyx route>}
    """

    error_pages: dict[str, Any]
    not_found_pages: dict[str, Any]

    @property
    def has_error_pages(self) -> bool:
        return bool(self.error_pages)

    @property
    def has_not_found_pages(self) -> bool:
        return bool(self.not_found_pages)

    def find_error_boundary(self, route_path: str) -> Optional[Any]:
        """Find the nearest ``error.pyx`` for *route_path* by walking up the tree."""
        return _walk_up(route_path, self.error_pages)

    def find_not_found_boundary(self, route_path: str) -> Optional[Any]:
        """Find the nearest ``not-found.pyx`` for *route_path*."""
        return _walk_up(route_path, self.not_found_pages)


def build_error_boundary_registry(
    pages: Sequence[Any],
) -> ErrorBoundaryRegistry:
    """Build an :class:`ErrorBoundaryRegistry` from page routes.

    This function takes the *full* list of compiled error/not-found page
    routes and indexes them by their parent directory.
    """

    error_pages: dict[str, Any] = {}
    not_found_pages: dict[str, Any] = {}

    for page in pages:
        name = page.source_relative_path.name.lower()
        parent = page.source_relative_path.parent.as_posix()
        # Normalise root directory to "."
        if not parent or parent == ".":
            parent = "."

        if name in _ERROR_FILENAMES:
            error_pages[parent] = page
        elif name in _NOT_FOUND_FILENAMES:
            not_found_pages[parent] = page

    return ErrorBoundaryRegistry(
        error_pages=error_pages,
        not_found_pages=not_found_pages,
    )


def _walk_up(route_path: str, registry: dict[str, Any]) -> Optional[Any]:
    """Walk up directory segments of *route_path* looking for a matching page.

    For ``/dashboard/settings/profile`` the lookup order is:

        1. ``"dashboard/settings/profile"``
        2. ``"dashboard/settings"``
        3. ``"dashboard"``
        4. ``"."``  (root)
    """

    # Normalise: strip leading/trailing slashes, collapse empty to root.
    stripped = route_path.strip("/")
    if not stripped:
        return registry.get(".")

    parts = stripped.split("/")

    # Walk from the deepest directory towards root.
    for end in range(len(parts), 0, -1):
        candidate = "/".join(parts[:end])
        if candidate in registry:
            return registry[candidate]

    return registry.get(".")


__all__ = [
    "ErrorBoundaryRegistry",
    "build_error_boundary_registry",
    "is_error_boundary_file",
    "is_error_page",
    "is_not_found_page",
]
