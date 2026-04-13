"""CSRF protection middleware using the double-submit cookie pattern.

The middleware sets a ``pyxle-csrf`` cookie on every response. Requests that
use state-changing methods (POST, PUT, PATCH, DELETE) must echo the cookie
value back via the ``X-CSRF-Token`` header **or** a ``_csrf_token`` form
field. If the values do not match, the request is rejected with 403.

Safe methods (GET, HEAD, OPTIONS, TRACE) are never checked.

Usage::

    from pyxle.devserver.csrf import CsrfMiddleware
    from starlette.middleware import Middleware

    middleware = [Middleware(CsrfMiddleware, secret="...")]
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Sequence

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
_COOKIE_NAME = "pyxle-csrf"
_HEADER_NAME = "x-csrf-token"
_FORM_FIELD = "_csrf_token"
_TOKEN_LENGTH = 32

_logger = logging.getLogger(__name__)


class CsrfMiddleware:
    """Double-submit cookie CSRF protection.

    Parameters
    ----------
    app:
        The ASGI application to wrap.
    secret:
        A server-side secret used to sign CSRF tokens. Should be sourced from
        ``PYXLE_SECRET_KEY`` or a similar environment variable.
    cookie_name:
        Name of the CSRF cookie (default ``pyxle-csrf``).
    header_name:
        Name of the request header containing the CSRF token
        (default ``x-csrf-token``).
    cookie_secure:
        Set the ``Secure`` flag on the cookie. ``True`` in production.
    cookie_samesite:
        ``SameSite`` attribute for the cookie (default ``"lax"``).
    exempt_paths:
        URL path prefixes exempt from CSRF checks (e.g., ``/api/webhooks``).
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        secret: str = "",
        cookie_name: str = _COOKIE_NAME,
        header_name: str = _HEADER_NAME,
        cookie_secure: bool = False,
        cookie_samesite: str = "lax",
        exempt_paths: Sequence[str] = (),
    ) -> None:
        self.app = app
        self._secret = secret
        self._cookie_name = cookie_name
        self._header_name = header_name.lower()
        self._cookie_secure = cookie_secure
        self._cookie_samesite = cookie_samesite
        self._exempt_paths: tuple[str, ...] = tuple(exempt_paths)

        if not self._secret:
            _logger.warning(
                "CsrfMiddleware: no secret key provided (PYXLE_SECRET_KEY). "
                "HMAC token verification is disabled — tokens are validated "
                "by double-submit comparison only."
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        method = request.method.upper()

        if method not in _SAFE_METHODS and not self._is_exempt(request.url.path):
            cookie_token = request.cookies.get(self._cookie_name, "")
            header_token = request.headers.get(self._header_name, "")

            # Also check form field for progressive enhancement
            submitted_token = header_token
            if not submitted_token:
                # Only attempt form body parsing when content type suggests it.
                content_type = (request.headers.get("content-type") or "").lower()
                if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    try:
                        form_data = await request.form()
                        submitted_token = form_data.get(_FORM_FIELD, "")
                    except Exception as exc:
                        _logger.debug("CSRF form body parsing failed: %s", exc)
                        submitted_token = ""

            if not cookie_token or not submitted_token:
                response = JSONResponse(
                    {"ok": False, "error": "CSRF token missing"},
                    status_code=403,
                )
                await response(scope, receive, send)
                return

            if not _tokens_match(cookie_token, submitted_token, self._secret):
                response = JSONResponse(
                    {"ok": False, "error": "CSRF token mismatch"},
                    status_code=403,
                )
                await response(scope, receive, send)
                return

        # Reuse the existing valid cookie token when available to avoid
        # race conditions with concurrent requests (M-9).  Only mint a
        # fresh token when no valid cookie is present.
        existing_cookie = request.cookies.get(self._cookie_name, "")
        if existing_cookie and _verify_token_integrity(existing_cookie, self._secret):
            token = existing_cookie
        else:
            token = _generate_token(self._secret)

        async def send_with_cookie(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                cookie_value = (
                    f"{self._cookie_name}={token}; Path=/"
                    f"; SameSite={self._cookie_samesite}"
                )
                if self._cookie_secure:
                    cookie_value += "; Secure"
                headers.append((b"set-cookie", cookie_value.encode("latin-1")))
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_cookie)

    def _is_exempt(self, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in self._exempt_paths)


def _generate_token(secret: str) -> str:
    """Generate a CSRF token (random value signed with the secret)."""
    raw = secrets.token_urlsafe(_TOKEN_LENGTH)
    if secret:
        sig = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{raw}.{sig}"
    return raw


def _compute_signature(raw: str, secret: str) -> str:
    """Compute the HMAC-SHA256 signature for a raw token value."""
    return hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:16]


def _verify_token_integrity(token: str, secret: str) -> bool:
    """Check that a token's HMAC signature is valid (when a secret is set).

    Returns ``True`` if the token is structurally valid.  For unsigned tokens
    (no secret), any non-empty token is considered valid.
    """
    if not token:
        return False
    if not secret:
        # No secret → unsigned tokens; any non-empty value is acceptable.
        return True
    if "." not in token:
        return False
    raw, _, sig = token.rpartition(".")
    if not raw or not sig:
        return False
    expected = _compute_signature(raw, secret)
    return hmac.compare_digest(sig, expected)


def _tokens_match(cookie_token: str, submitted_token: str, secret: str) -> bool:
    """Validate that the submitted token matches the cookie token.

    Performs two checks:

    1. **Double-submit comparison** — the submitted token must match the
       cookie token (constant-time).
    2. **HMAC signature verification** (when a secret is configured) —
       the cookie token's signature must be valid.  This prevents an
       attacker who can set arbitrary cookies from forging tokens.
    """
    if not cookie_token or not submitted_token:
        return False

    # Double-submit: submitted value must match cookie value.
    if not hmac.compare_digest(cookie_token, submitted_token):
        return False

    # HMAC integrity: verify the cookie token was minted by this server.
    if not _verify_token_integrity(cookie_token, secret):
        return False

    return True


__all__ = ["CsrfMiddleware"]
