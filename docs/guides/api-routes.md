# API Routes

Files under `pages/api/` are API endpoints. They are plain Python files (not `.pyx`) that handle HTTP requests and return JSON or other responses.

## Basic API route

Create `pages/api/hello.py`:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

async def get(request: Request) -> JSONResponse:
    return JSONResponse({"message": "Hello, world!"})
```

This responds to `GET /api/hello`:

```bash
curl http://localhost:8000/api/hello
# {"message": "Hello, world!"}
```

## HTTP methods

Define functions named after HTTP methods:

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

async def get(request: Request) -> JSONResponse:
    users = await fetch_all_users()
    return JSONResponse({"users": users})

async def post(request: Request) -> JSONResponse:
    body = await request.json()
    user = await create_user(body["name"], body["email"])
    return JSONResponse({"user": user}, status_code=201)

async def delete(request: Request) -> JSONResponse:
    body = await request.json()
    await remove_user(body["id"])
    return JSONResponse({"deleted": True})
```

Supported methods: `get`, `post`, `put`, `patch`, `delete`, `options`.

Requests to unsupported methods return `405 Method Not Allowed`.

## Using HTTPEndpoint classes

For more structure, use Starlette's `HTTPEndpoint`:

```python
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

class Users(HTTPEndpoint):
    async def get(self, request: Request) -> JSONResponse:
        return JSONResponse({"users": []})

    async def post(self, request: Request) -> JSONResponse:
        body = await request.json()
        return JSONResponse({"created": True}, status_code=201)
```

## Dynamic API routes

Use the same bracket syntax as page routes:

```
pages/api/users/[id].py  -->  /api/users/:id
```

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

async def get(request: Request) -> JSONResponse:
    user_id = request.path_params["id"]
    user = await fetch_user(user_id)
    if user is None:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"user": user})
```

## Reading request bodies

```python
async def post(request: Request) -> JSONResponse:
    # JSON body
    body = await request.json()

    # Form data
    form = await request.form()

    # Raw body
    raw = await request.body()

    return JSONResponse({"received": True})
```

## Error responses

Return appropriate HTTP status codes:

```python
async def get(request: Request) -> JSONResponse:
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return JSONResponse({"error": "Missing API key"}, status_code=401)

    data = await fetch_data(api_key)
    if data is None:
        return JSONResponse({"error": "Not found"}, status_code=404)

    return JSONResponse({"data": data})
```

## API routes vs server actions

| Feature | API routes | Server actions |
|---------|-----------|----------------|
| File location | `pages/api/*.py` | Inside `.pyx` files |
| HTTP methods | Any (GET, POST, PUT, etc.) | POST only |
| Response format | Any Starlette Response | JSON dict |
| Called from | Anywhere (curl, fetch, etc.) | `<Form>` or `useAction` |
| CSRF protection | Not by default | Enabled by default |
| Use case | Public APIs, webhooks, integrations | Form submissions, mutations |

## Next steps

- Add middleware to your routes: [Middleware](middleware.md)
- Protect routes with CSRF: [Security](security.md)
