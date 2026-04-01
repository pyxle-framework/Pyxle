# `.pyx` Files

A `.pyx` file is the fundamental building block of a Pyxle application. It combines Python server logic with a React component in a single file -- your data fetching and your UI live together.

## Anatomy of a `.pyx` file

A `.pyx` file has up to three sections:

```python
# 1. Python section -- runs on the server
from datetime import datetime

HEAD = '<title>My Page</title>'

@server
async def load_page(request):
    return {"now": datetime.now().isoformat()}
```

```jsx
// 2. JSX section -- runs on both server (SSR) and client
export default function MyPage({ data }) {
  return <h1>Current time: {data.now}</h1>;
}
```

The compiler automatically detects which lines are Python and which are JSX. Python code uses `@server`/`@action` decorators, imports, and standard Python syntax. Everything else is treated as JSX.

## The Python section

The Python section runs entirely on the server. It can:

- **Import modules** -- any Python package available in your environment
- **Define a `HEAD` variable** -- static or dynamic `<head>` elements
- **Define a `@server` loader** -- an async function that fetches data for the component
- **Define `@action` mutations** -- async functions callable from the client

```python
from pyxle.runtime import server, action
import httpx

HEAD = '<title>Users</title>'

@server
async def load_users(request):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.example.com/users")
    return {"users": resp.json()}

@action
async def delete_user(request):
    body = await request.json()
    user_id = body["id"]
    # ... delete from database ...
    return {"deleted": user_id}
```

### Rules for the Python section

- **One `@server` loader per file.** The loader receives a Starlette `Request` and must return a JSON-serializable dict.
- **Multiple `@action` functions are allowed.** Each becomes a callable endpoint.
- **The `@server` function must be `async`.** Pyxle enforces this at compile time.
- **Imports are auto-detected.** Lines starting with `import` or `from` are classified as Python.
- **The `@server` and `@action` decorators are available globally** -- you do not need to import them (the compiler injects the import automatically).

## The JSX section

The JSX section is a standard React component. It runs on both the server (for SSR) and the client (for hydration and interactivity).

```jsx
export default function MyPage({ data }) {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <h1>Users: {data.users.length}</h1>
      <button onClick={() => setCount(c => c + 1)}>
        Clicked {count} times
      </button>
    </div>
  );
}
```

### Rules for the JSX section

- **Must have a default export.** The default export is the page component.
- **Receives `{ data }` as props.** The `data` prop contains whatever the `@server` loader returned. If there is no loader, `data` is an empty object `{}`.
- **Can import from `pyxle/client`.** This gives you `<Head>`, `<Script>`, `<Image>`, `<ClientOnly>`, `<Form>`, `useAction`, `<Link>`, `navigate`, and `prefetch`.
- **Can import from `node_modules`.** Any npm package in your `package.json` is available.
- **Cannot import Python code.** The Python and JSX sections are compiled separately.

## The `HEAD` variable

The `HEAD` variable controls what goes in the document `<head>`:

```python
# Static HEAD -- a string or list of strings
HEAD = '<title>About Us</title><meta name="description" content="Our story" />'

# Or as a list
HEAD = [
    '<title>About Us</title>',
    '<meta name="description" content="Our story" />',
]
```

For dynamic head content that depends on loader data, use a callable:

```python
@server
async def load_post(request):
    post = await fetch_post(request.path_params["slug"])
    return {"post": post}

HEAD = lambda data: [
    f'<title>{data["post"]["title"]}</title>',
    f'<meta name="description" content="{data["post"]["excerpt"]}" />',
]
```

Dynamic `HEAD` values are automatically sanitised to prevent XSS injection -- angle brackets inside `<title>` text are escaped, event handler attributes are stripped, and `javascript:` URLs are neutralised.

See [Head Management](../guides/head-management.md) for full details.

## A complete example

```python
from datetime import datetime, timezone

HEAD = lambda data: f'<title>{data["greeting"]}</title>'

@server
async def load_home(request):
    hour = datetime.now(tz=timezone.utc).hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return {"greeting": greeting}
```

```jsx
export default function HomePage({ data }) {
  return (
    <main>
      <h1>{data.greeting}</h1>
      <p>Welcome to Pyxle.</p>
    </main>
  );
}
```

## JSX-only files

If a page has no server logic, you can write a JSX-only `.pyx` file:

```jsx
export default function AboutPage() {
  return (
    <main>
      <h1>About</h1>
      <p>This page has no loader -- it renders the same content every time.</p>
    </main>
  );
}
```

## Next steps

- Learn how files map to URLs: [Routing](routing.md)
- Add data fetching: [Data Loading](data-loading.md)
