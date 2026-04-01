# Runtime API Reference

The `pyxle.runtime` module provides decorators and error classes used in `.pyx` files. These are automatically available in the Python section of every `.pyx` file -- you do not need to import them (the compiler injects the import).

## `@server`

Marks an async function as a page data loader.

```python
@server
async def load_page(request):
    return {"key": "value"}
```

**Behaviour:**

- Attaches `__pyxle_loader__ = True` to the function (no wrapping)
- The function must be `async` (enforced at compile time)
- Receives a Starlette [`Request`](https://www.starlette.io/requests/) object
- Must return a JSON-serializable `dict`
- Can return a `(dict, int)` tuple to set the HTTP status code
- Only one `@server` function is allowed per `.pyx` file

**Request object properties:**

| Property | Type | Description |
|----------|------|-------------|
| `request.path_params` | `dict` | URL path parameters from dynamic routes |
| `request.query_params` | `QueryParams` | URL query string parameters |
| `request.headers` | `Headers` | HTTP request headers |
| `request.cookies` | `dict` | Request cookies |
| `request.url` | `URL` | Full request URL |
| `request.method` | `str` | HTTP method |
| `request.state` | `State` | Mutable state for middleware to attach data |

## `@action`

Marks an async function as a server action callable from React components.

```python
@action
async def create_item(request):
    body = await request.json()
    return {"id": 1, "name": body["name"]}
```

**Behaviour:**

- Attaches `__pyxle_action__ = True` to the function (no wrapping)
- The function must be `async`
- Receives a Starlette `Request` object
- Must return a JSON-serializable `dict`
- Multiple `@action` functions are allowed per `.pyx` file
- Accessible via `POST /api/__actions/{page_path}/{action_name}`
- Protected by CSRF middleware by default

**Client response format:**

```json
// Success
{ "ok": true, "id": 1, "name": "Item" }

// Error (from ActionError)
{ "ok": false, "error": "Error message" }
```

## `LoaderError`

Exception class for structured loader errors. Triggers the nearest `error.pyx` boundary.

```python
from pyxle.runtime import LoaderError

@server
async def load_page(request):
    raise LoaderError("Not found", status_code=404, data={"id": 42})
```

**Constructor:**

```python
LoaderError(message: str, status_code: int = 500, data: dict | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | (required) | Error message displayed in the error boundary |
| `status_code` | `int` | `500` | HTTP response status code |
| `data` | `dict \| None` | `None` | Additional JSON-serializable context |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `.message` | `str` | The error message |
| `.status_code` | `int` | HTTP status code |
| `.data` | `dict` | Additional context (empty dict if None was passed) |

## `ActionError`

Exception class for structured action errors. Returns a JSON error response to the client.

```python
from pyxle.runtime import ActionError

@action
async def update_item(request):
    raise ActionError("Validation failed", status_code=400, data={"field": "name"})
```

**Constructor:**

```python
ActionError(message: str, status_code: int = 400, data: dict | None = None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | (required) | Error message sent to the client |
| `status_code` | `int` | `400` | HTTP response status code |
| `data` | `dict \| None` | `None` | Additional JSON-serializable payload |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `.message` | `str` | The error message |
| `.status_code` | `int` | HTTP status code |
| `.data` | `dict` | Additional data (empty dict if None was passed) |

## `HEAD` variable

Not part of `pyxle.runtime` but available in every `.pyx` file. Controls document `<head>` elements.

**Static form:**

```python
# String
HEAD = '<title>Page Title</title>'

# List of strings
HEAD = ['<title>Page Title</title>', '<meta name="description" content="..." />']
```

**Dynamic form (callable):**

```python
HEAD = lambda data: f'<title>{data["title"]}</title>'
```

The callable receives the loader's return value. Must return a string or list of strings synchronously.

## Explicit imports

While the compiler auto-injects `@server` and `@action`, you can also import explicitly:

```python
from pyxle.runtime import server, action, LoaderError, ActionError
```

This is useful for type checking and IDE support.
