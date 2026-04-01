# Routing

Pyxle uses **file-based routing**. The file structure inside your `pages/` directory determines the URL routes of your application. No router configuration is needed.

## Basic routes

Every `.pyx` file in `pages/` becomes a route:

| File | URL |
|------|-----|
| `pages/index.pyx` | `/` |
| `pages/about.pyx` | `/about` |
| `pages/contact.pyx` | `/contact` |
| `pages/blog/index.pyx` | `/blog` |
| `pages/blog/archive.pyx` | `/blog/archive` |

The `index.pyx` filename is special -- it maps to the parent directory's path.

## Dynamic segments

Wrap a filename segment in square brackets to create a dynamic route parameter:

| File | URL Pattern | Example |
|------|-------------|---------|
| `pages/blog/[slug].pyx` | `/blog/:slug` | `/blog/hello-world` |
| `pages/users/[id].pyx` | `/users/:id` | `/users/42` |
| `pages/[category]/[id].pyx` | `/:category/:id` | `/electronics/99` |

Access dynamic parameters in your loader via `request.path_params`:

```python
@server
async def load_post(request):
    slug = request.path_params["slug"]
    post = await fetch_post(slug)
    return {"post": post}
```

```jsx
export default function BlogPost({ data }) {
  return <h1>{data.post.title}</h1>;
}
```

### Parameter name rules

- Hyphens in parameter names become underscores: `[user-id].pyx` --> `request.path_params["user_id"]`
- The parameter name is sanitised to be a valid Python identifier

## Catch-all routes

Use `[...param].pyx` to match any number of path segments:

| File | URL Pattern | Example Matches |
|------|-------------|----------------|
| `pages/docs/[...slug].pyx` | `/docs/*` | `/docs/getting-started`, `/docs/api/config` |

The parameter captures the entire remaining path as a string:

```python
@server
async def load_docs(request):
    slug = request.path_params["slug"]  # "getting-started" or "api/config"
    return {"slug": slug}
```

## Optional catch-all routes

Use `[[...param]].pyx` (double brackets) to match the parent path **and** any sub-paths:

| File | URL Pattern | Example Matches |
|------|-------------|----------------|
| `pages/docs/[[...slug]].pyx` | `/docs` and `/docs/*` | `/docs`, `/docs/intro`, `/docs/api/ref` |

This creates two routes: one for the exact parent path and one for the catch-all.

## Route groups

Wrap a directory name in parentheses to **exclude it from the URL**:

```
pages/
  (marketing)/
    pricing.pyx      -->  /pricing     (not /marketing/pricing)
    features.pyx     -->  /features
  (dashboard)/
    settings.pyx     -->  /settings
    profile.pyx      -->  /profile
```

Route groups let you organise files by concern without affecting URLs.

## API routes

Python files under `pages/api/` become API endpoints:

| File | URL |
|------|-----|
| `pages/api/pulse.py` | `/api/pulse` |
| `pages/api/users.py` | `/api/users` |
| `pages/api/users/[id].py` | `/api/users/:id` |

API routes are standard Python files (not `.pyx`). See [API Routes](../guides/api-routes.md) for details.

## Viewing your route table

Run `pyxle routes` to see all registered routes:

```bash
pyxle routes

# Or as JSON:
pyxle routes --json
```

## Special files

These filenames have special meaning and do not create their own routes:

| File | Purpose |
|------|---------|
| `layout.pyx` | Wraps sibling and descendant pages in a shared layout |
| `template.pyx` | Like layout but resets state on navigation |
| `error.pyx` | Error boundary for sibling and descendant pages |
| `not-found.pyx` | 404 page for the current directory scope |

See [Layouts](layouts.md) and [Error Handling](../guides/error-handling.md).

## Next steps

- Load data for your pages: [Data Loading](data-loading.md)
- Wrap pages in shared layouts: [Layouts](layouts.md)
