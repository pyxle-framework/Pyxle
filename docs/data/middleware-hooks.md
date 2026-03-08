# Custom Middleware & Route Hooks

Pyxle lets you extend both the Starlette middleware stack and per-route behaviour without forking the dev server.

-## Global middleware (`pyxle.config.json`)

```json
{
  "middleware": ["middlewares.telemetry.trace"],
  "routeMiddleware": {
    "pages": ["middlewares.telemetry.enforce_csp"],
    "apis": ["middlewares.telemetry.attach_request_id"]
  }
}
```

- `middleware` entries should point to dotted paths that resolve to middleware specs. Supported forms include:
  - callables returning `starlette.middleware.Middleware` objects or `(MiddlewareClass, <options>)` tuples,
  - ASGI middleware classes (typically `BaseHTTPMiddleware` subclasses or any class accepting `(app, **kwargs)`), and
  - pre-built `Middleware` instances when configuration is captured at import time.
- Page/API route middleware use the same format but only wrap their respective routers.
- The loader in `pyxle/devserver/middleware.py` resolves dotted import strings, validates callables, and raises `MiddlewareHookError` when something cannot be imported.

## Route hooks

For more targeted logic (timing, auth, custom headers) use route hooks.

```python
# middlewares/telemetry.py
import time
from pyxle.devserver.route_hooks import RouteHook, RouteContext

class LogDuration(RouteHook):
    async def on_pre_call(self, request, context: RouteContext):
        request.state.start_ns = time.perf_counter_ns()

    async def on_post_call(self, request, response, context):
        elapsed = (time.perf_counter_ns() - request.state.start_ns) / 1e6
        print(f"{context.path} took {elapsed:.2f}ms")
```

`RouteHook` provides lifecycle helpers (`on_pre_call`, `on_post_call`, `on_error`) so the framework automatically calls the right callbacks before and after the handler when the hook is registered. You can also register async functions that match `(context, request, call_next)` or callables that return them.

Add the dotted path to `routeMiddleware.pages` or `.apis`. Hooks run in this order:

1. `on_pre_call`
2. Handler execution
3. `on_post_call`
4. `on_error` if an exception bubbles up

Default hooks (`DEFAULT_PAGE_POLICIES`, `DEFAULT_API_POLICIES`) already enforce basics like allowing only `GET` for pages and validating `HEAD` metadata.

## Compare with Next.js

This is similar to Next.js Middleware + Route Handlers, except you control plain Starlette middleware classes and hook objects. There is no Edge runtime—everything runs inside the same Uvicorn worker alongside your loaders.

Related docs:
- [Configuration reference](../reference/config.md)
- [Dev server internals](../devserver/dev-server.md)

---
**Navigation:** [← Previous](api-routes.md) | [Next →](../styling/index.md)
