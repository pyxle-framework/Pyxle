# Error Handling

Pyxle provides structured error handling through error exceptions, error boundaries, and not-found pages.

## LoaderError

Raise `LoaderError` from a `@server` function to trigger the nearest error boundary:

```python
from pyxle.runtime import LoaderError

@server
async def load_user(request):
    user = await db.get_user(request.path_params["id"])
    if user is None:
        raise LoaderError("User not found", status_code=404)
    return {"user": user}
```

### LoaderError parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | (required) | Error message shown in the error boundary |
| `status_code` | `int` | `500` | HTTP status code for the response |
| `data` | `dict` | `{}` | Additional context passed to the error boundary |

## ActionError

Raise `ActionError` from an `@action` function to return a structured error to the client:

```python
from pyxle.runtime import ActionError

@action
async def update_profile(request):
    body = await request.json()
    if len(body.get("name", "")) < 2:
        raise ActionError("Name must be at least 2 characters", status_code=400)
    # ...
    return {"updated": True}
```

The client receives `{ "ok": false, "error": "Name must be at least 2 characters" }`.

### ActionError parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | `str` | (required) | Error message sent to the client |
| `status_code` | `int` | `400` | HTTP status code |
| `data` | `dict` | `{}` | Additional data in the error response |

## Error boundaries (`error.pyxl`)

Create an `error.pyxl` file to catch errors from pages in the same directory and below:

```
pages/
  error.pyxl          # Catches errors from all pages
  index.pyxl
  dashboard/
    error.pyxl        # Catches errors from dashboard pages only
    index.pyxl
    settings.pyxl
```

An error boundary is a React component that receives the error context as props:

```jsx
// pages/error.pyxl
export default function ErrorPage({ error }) {
  return (
    <div>
      <h1>Something went wrong</h1>
      <p>{error.message}</p>
      <p>Status: {error.statusCode}</p>
      <a href="/">Go home</a>
    </div>
  );
}
```

### Error props

The `error` prop contains:

| Property | Type | Description |
|----------|------|-------------|
| `message` | `string` | The error message |
| `statusCode` | `number` | HTTP status code |
| `type` | `string` | Exception class name |
| `data` | `object?` | Additional data (if provided via `LoaderError(data=...)`) |

### Boundary resolution

When an error occurs, Pyxle walks up the directory tree from the page that failed until it finds an `error.pyxl`:

- `pages/dashboard/settings.pyxl` throws -->
  1. Check `pages/dashboard/error.pyxl`
  2. Check `pages/error.pyxl`
  3. Use default error document

## Not-found pages (`not-found.pyxl`)

Create a `not-found.pyxl` file to customise the 404 page:

```jsx
// pages/not-found.pyxl
export default function NotFoundPage() {
  return (
    <div>
      <h1>404 - Page Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <a href="/">Go home</a>
    </div>
  );
}
```

Like error boundaries, not-found pages follow directory scoping -- a `not-found.pyxl` in `pages/docs/` handles 404s within `/docs/*`.

## Dev mode error overlay

During development (`pyxle dev`), errors also appear in a browser overlay with:

- The error message and stack trace
- Breadcrumbs showing which stage failed (loader, renderer, hydration)
- File path and line number

The overlay communicates via WebSocket and updates in real time as you fix errors.

## Next steps

- Add client-side components: [Client Components](client-components.md)
- Secure your application: [Security](security.md)
