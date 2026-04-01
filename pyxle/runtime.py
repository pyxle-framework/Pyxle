"""Runtime helpers exposed to compiled Pyxle artifacts."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def server(function: F) -> F:
    """Mark a function as a Pyxle loader and return it unchanged.

    The decorator intentionally performs no wrapping so the original coroutine
    signature and attributes remain available to the runtime. It simply tags the
    function for future inspection by attaching ``__pyxle_loader__ = True``.
    """

    setattr(function, "__pyxle_loader__", True)
    return function


def action(function: F) -> F:
    """Mark a function as a Pyxle server action and return it unchanged.

    Server actions are async functions callable from React components via the
    ``useAction`` hook. They receive the full Starlette ``Request`` object and
    must return a JSON-serializable dict. The decorator adds no wrapping — it
    only tags the function with ``__pyxle_action__ = True`` for compiler and
    runtime inspection.

    Raise ``ActionError`` from within an action to return a structured error
    response to the client with a specific HTTP status code.
    """

    setattr(function, "__pyxle_action__", True)
    return function


class ActionError(Exception):
    """Raise from within a ``@action`` function to return a structured error.

    The ``message`` is forwarded to the client. ``status_code`` controls the
    HTTP response status (default 400). ``data`` carries any additional
    JSON-serializable payload included in the error response.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data or {}


class LoaderError(Exception):
    """Raise from a ``@server`` loader to trigger the nearest error boundary.

    When raised, the framework renders the closest ``error.pyx`` page up the
    directory tree from the current route, passing the error context as props.
    If no ``error.pyx`` is found, the default error document is used.

    The ``message`` is visible in the rendered error page. ``status_code``
    controls the HTTP response status (default 500). ``data`` carries any
    additional JSON-serializable context passed to the error boundary.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data or {}


__all__ = ["server", "action", "ActionError", "LoaderError"]
