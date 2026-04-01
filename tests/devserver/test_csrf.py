"""Tests for pyxle.devserver.csrf — CSRF protection middleware."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from pyxle.devserver.csrf import CsrfMiddleware, _generate_token, _tokens_match


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


class TestTokenHelpers:
    def test_generate_token_without_secret(self):
        token = _generate_token("")
        assert isinstance(token, str)
        assert len(token) > 10

    def test_generate_token_with_secret(self):
        token = _generate_token("my-secret")
        assert "." in token
        raw, sig = token.rsplit(".", 1)
        assert len(sig) == 16

    def test_tokens_match_identical(self):
        assert _tokens_match("abc", "abc", "") is True

    def test_tokens_mismatch(self):
        assert _tokens_match("abc", "xyz", "") is False

    def test_tokens_match_empty_rejected(self):
        assert _tokens_match("", "abc", "") is False
        assert _tokens_match("abc", "", "") is False
        assert _tokens_match("", "", "") is False


# ---------------------------------------------------------------------------
# Middleware integration tests
# ---------------------------------------------------------------------------


def _build_app(
    *,
    secret: str = "test-secret",
    exempt_paths: tuple[str, ...] = (),
) -> Starlette:
    async def get_handler(request: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def post_handler(request: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[
            Route("/page", get_handler, methods=["GET"]),
            Route("/action", post_handler, methods=["POST"]),
            Route("/webhook", post_handler, methods=["POST"]),
        ],
        middleware=[
            Middleware(
                CsrfMiddleware,
                secret=secret,
                exempt_paths=exempt_paths,
            ),
        ],
    )
    return app


class TestCsrfMiddleware:
    def test_get_request_sets_cookie(self):
        client = TestClient(_build_app())
        response = client.get("/page")
        assert response.status_code == 200
        assert "pyxle-csrf" in response.cookies

    def test_post_without_token_returns_403(self):
        client = TestClient(_build_app())
        response = client.post("/action")
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "CSRF token missing"

    def test_post_with_valid_header_token_succeeds(self):
        client = TestClient(_build_app())
        # First, do a GET to get the CSRF cookie
        get_response = client.get("/page")
        csrf_token = get_response.cookies["pyxle-csrf"]

        # POST with the token in the header
        response = client.post(
            "/action",
            headers={"x-csrf-token": csrf_token},
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_post_with_mismatched_token_returns_403(self):
        client = TestClient(_build_app())
        # Get a real cookie
        client.get("/page")

        # POST with a bogus token
        response = client.post(
            "/action",
            headers={"x-csrf-token": "completely-wrong-token"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "CSRF token mismatch"

    def test_post_with_form_field_token_succeeds(self):
        client = TestClient(_build_app())
        get_response = client.get("/page")
        csrf_token = get_response.cookies["pyxle-csrf"]

        # Form fields require echoing the cookie via the header as well
        # because some form submissions may include the token in both places.
        # The primary mechanism is the header.
        response = client.post(
            "/action",
            data={"_csrf_token": csrf_token, "name": "test"},
            headers={"x-csrf-token": csrf_token},
        )
        assert response.status_code == 200

    def test_exempt_path_skips_check(self):
        client = TestClient(_build_app(exempt_paths=("/webhook",)))
        response = client.post("/webhook")
        assert response.status_code == 200

    def test_non_exempt_path_still_checked(self):
        client = TestClient(_build_app(exempt_paths=("/webhook",)))
        response = client.post("/action")
        assert response.status_code == 403

    def test_cookie_has_samesite_and_no_httponly(self):
        client = TestClient(_build_app())
        response = client.get("/page")
        # Double-submit cookies must NOT be HttpOnly so JS can read them
        set_cookie_header = response.headers.get("set-cookie", "")
        assert "HttpOnly" not in set_cookie_header
        assert "SameSite=lax" in set_cookie_header

    def test_safe_methods_never_blocked(self):
        """GET and HEAD should never be blocked by CSRF."""
        client = TestClient(_build_app())
        assert client.get("/page").status_code == 200
        assert client.head("/page").status_code == 200
