from __future__ import annotations

from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from pyxle.devserver.route_hooks import RouteContext, RouteHook


class HeaderCaptureMiddleware(BaseHTTPMiddleware):
    """Test middleware that echoes a header back to the client."""

    async def dispatch(self, request: Request, call_next):
        value = request.headers.get("x-auth-token", "")
        response = await call_next(request)
        if value:
            response.headers["x-auth-token"] = value
        return response


class SimpleAsgiMiddleware:
    """Minimal ASGI middleware implemented without Starlette helpers."""

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        return await self._app(scope, receive, send)


def create_rate_limit_middleware() -> Middleware:
    class _RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.rate_limit_checked = True
            response = await call_next(request)
            response.headers["x-rate-limit"] = "ok"
            return response

    return Middleware(_RateLimitMiddleware)


def invalid_factory():
    return "not-a-middleware"


class ConfigurableSuffixMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, suffix: str = ""):
        super().__init__(app)
        self._suffix = suffix

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if self._suffix:
            response.headers["x-config-suffix"] = self._suffix
        return response


def tuple_middleware_factory():
    return (ConfigurableSuffixMiddleware, {"suffix": "beta"})


async def record_route_hook(context, request, call_next):
    request.state.recorded_route = context.path
    return await call_next(request)


def build_target_hook():
    async def _hook(context, request, call_next):
        markers = getattr(request.state, "route_targets", [])
        markers = list(markers)
        markers.append(context.target)
        request.state.route_targets = markers
        return await call_next(request)

    return _hook


def invalid_route_hook_factory():
    return "not-an-async-hook"


class LifecycleRecordingHook(RouteHook):
    async def on_pre_call(self, request: Request, context: RouteContext) -> None:
        markers = getattr(request.state, "hook_markers", [])
        markers = list(markers)
        markers.append("pre")
        request.state.hook_markers = markers

    async def on_post_call(
        self, request: Request, response: PlainTextResponse, context: RouteContext
    ) -> None:
        markers = getattr(request.state, "hook_markers", [])
        markers = list(markers)
        markers.append("post")
        request.state.hook_markers = markers
