"""Tests for error boundary integration in pyxle.ssr.view."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock


from pyxle.devserver.error_pages import ErrorBoundaryRegistry
from pyxle.devserver.routes import PageRoute
from pyxle.runtime import ActionError, LoaderError
from pyxle.ssr.view import (
    _build_error_context,
    _try_error_boundary,
    build_not_found_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_page_route(
    path: str = "/test",
    source_rel: str = "test.pyx",
) -> PageRoute:
    return PageRoute(
        path=path,
        source_relative_path=Path(source_rel),
        source_absolute_path=Path("/project/pages") / source_rel,
        server_module_path=Path("/build/server/pages") / Path(source_rel).with_suffix(".py"),
        client_module_path=Path("/build/client") / Path(source_rel).with_suffix(".jsx"),
        metadata_path=Path("/build/metadata/pages") / Path(source_rel).with_suffix(".json"),
        module_key=f"pyxle.server.pages.{Path(source_rel).stem}",
        client_asset_path=f"/{Path(source_rel).stem}.jsx",
        server_asset_path=f"pages/{Path(source_rel).stem}",
        content_hash="abc123",
        loader_name=None,
        loader_line=None,
        head_elements=(),
        head_is_dynamic=False,
    )


def _stub_request(path: str = "/test"):
    req = MagicMock()
    req.url.path = path
    req.headers = {}
    return req


# ---------------------------------------------------------------------------
# _build_error_context
# ---------------------------------------------------------------------------


class TestBuildErrorContext:
    def test_generic_exception(self):
        err = RuntimeError("something failed")
        ctx = _build_error_context(err, 500)
        assert ctx["message"] == "something failed"
        assert ctx["statusCode"] == 500
        assert ctx["type"] == "RuntimeError"

    def test_loader_error_uses_message_field(self):
        err = LoaderError("not authorized", status_code=403, data={"reason": "no token"})
        ctx = _build_error_context(err, 403)
        assert ctx["message"] == "not authorized"
        assert ctx["statusCode"] == 403
        assert ctx["data"] == {"reason": "no token"}

    def test_loader_error_without_data(self):
        err = LoaderError("oops")
        ctx = _build_error_context(err, 500)
        assert "data" not in ctx

    def test_action_error(self):
        err = ActionError("bad request", status_code=400, data={"field": "email"})
        ctx = _build_error_context(err, 400)
        assert ctx["message"] == "bad request"
        assert ctx["data"] == {"field": "email"}

    def test_action_error_without_data(self):
        err = ActionError("forbidden", status_code=403)
        ctx = _build_error_context(err, 403)
        assert "data" not in ctx


# ---------------------------------------------------------------------------
# _try_error_boundary
# ---------------------------------------------------------------------------


class TestTryErrorBoundary:
    def _error_page(self) -> PageRoute:
        return _stub_page_route(path="/error", source_rel="error.pyx")

    def _registry_with_root(self) -> ErrorBoundaryRegistry:
        return ErrorBoundaryRegistry(
            error_pages={".": self._error_page()},
            not_found_pages={},
        )

    def test_returns_none_when_no_registry(self):
        result = asyncio.run(
            _try_error_boundary(
                request=_stub_request(),
                settings=MagicMock(),
                renderer=MagicMock(),
                error_boundaries=None,
                route_path="/test",
                error=RuntimeError("fail"),
                status_code=500,
            )
        )
        assert result is None

    def test_returns_none_when_no_boundary_found(self):
        empty = ErrorBoundaryRegistry(error_pages={}, not_found_pages={})
        result = asyncio.run(
            _try_error_boundary(
                request=_stub_request(),
                settings=MagicMock(),
                renderer=MagicMock(),
                error_boundaries=empty,
                route_path="/test",
                error=RuntimeError("fail"),
                status_code=500,
            )
        )
        assert result is None

    def test_renders_error_boundary_when_found(self):
        mock_renderer = MagicMock()
        mock_render_result = MagicMock()
        mock_render_result.html = "<div>Error Page</div>"
        mock_render_result.inline_styles = ()
        mock_render_result.head_elements = ()
        mock_renderer.render = AsyncMock(return_value=mock_render_result)

        settings = MagicMock()
        settings.debug = False
        settings.vite_host = "127.0.0.1"
        settings.vite_port = 5173
        settings.page_manifest = None
        settings.global_stylesheets = ()

        result = asyncio.run(
            _try_error_boundary(
                request=_stub_request(),
                settings=settings,
                renderer=mock_renderer,
                error_boundaries=self._registry_with_root(),
                route_path="/test",
                error=LoaderError("broken", status_code=500),
                status_code=500,
            )
        )
        assert result is not None
        assert result.status_code == 500

    def test_uses_correct_status_code(self):
        mock_renderer = MagicMock()
        mock_render_result = MagicMock()
        mock_render_result.html = "<div>Not Found</div>"
        mock_render_result.inline_styles = ()
        mock_render_result.head_elements = ()
        mock_renderer.render = AsyncMock(return_value=mock_render_result)

        settings = MagicMock()
        settings.debug = False
        settings.vite_host = "127.0.0.1"
        settings.vite_port = 5173
        settings.page_manifest = None
        settings.global_stylesheets = ()

        result = asyncio.run(
            _try_error_boundary(
                request=_stub_request(),
                settings=settings,
                renderer=mock_renderer,
                error_boundaries=self._registry_with_root(),
                route_path="/test",
                error=LoaderError("gone", status_code=404),
                status_code=404,
            )
        )
        assert result is not None
        assert result.status_code == 404

    def test_returns_none_when_boundary_itself_fails(self):
        mock_renderer = MagicMock()
        mock_renderer.render = AsyncMock(side_effect=RuntimeError("boundary crashed"))

        result = asyncio.run(
            _try_error_boundary(
                request=_stub_request(),
                settings=MagicMock(),
                renderer=mock_renderer,
                error_boundaries=self._registry_with_root(),
                route_path="/test",
                error=RuntimeError("original"),
                status_code=500,
            )
        )
        assert result is None


# ---------------------------------------------------------------------------
# build_not_found_response
# ---------------------------------------------------------------------------


class TestBuildNotFoundResponse:
    def test_returns_none_without_registry(self):
        result = asyncio.run(
            build_not_found_response(
                request=_stub_request("/missing"),
                settings=MagicMock(),
                renderer=MagicMock(),
                error_boundaries=None,
            )
        )
        assert result is None

    def test_returns_none_without_not_found_boundary(self):
        empty = ErrorBoundaryRegistry(error_pages={}, not_found_pages={})
        result = asyncio.run(
            build_not_found_response(
                request=_stub_request("/missing"),
                settings=MagicMock(),
                renderer=MagicMock(),
                error_boundaries=empty,
            )
        )
        assert result is None

    def test_returns_none_when_boundary_fails(self):
        nf_page = _stub_page_route("/not-found", "not-found.pyx")
        registry = ErrorBoundaryRegistry(
            error_pages={},
            not_found_pages={".": nf_page},
        )

        mock_renderer = MagicMock()
        mock_renderer.render = AsyncMock(side_effect=RuntimeError("render fail"))

        settings = MagicMock()
        settings.debug = False
        settings.pages_dir = Path("/fake/pages")

        result = asyncio.run(
            build_not_found_response(
                request=_stub_request("/missing"),
                settings=settings,
                renderer=mock_renderer,
                error_boundaries=registry,
            )
        )
        assert result is None
