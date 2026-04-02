"""Health check endpoint. Visit /api/pulse to verify the server is running."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse

from pyxle import __version__


async def endpoint(request: Request) -> JSONResponse:
    return JSONResponse({
        "status": "ok",
        "pyxle": __version__,
    })
