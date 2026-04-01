# Head Management

Pyxle provides three ways to control the document `<head>`: the `HEAD` Python variable, the `<Head>` JSX component, and layout-level head elements. They merge together with automatic deduplication.

## The `HEAD` variable

Define a `HEAD` variable in the Python section of your `.pyx` file:

```python
# Static string
HEAD = '<title>My Page</title><meta name="description" content="Page description" />'

# Or a list of strings
HEAD = [
    '<title>My Page</title>',
    '<meta name="description" content="Page description" />',
    '<link rel="canonical" href="https://example.com/page" />',
]
```

### Dynamic HEAD

For head content that depends on loader data, use a callable:

```python
@server
async def load_post(request):
    post = await fetch_post(request.path_params["slug"])
    return {"post": post}

HEAD = lambda data: [
    f'<title>{data["post"]["title"]} - My Blog</title>',
    f'<meta name="description" content="{data["post"]["excerpt"]}" />',
    f'<meta property="og:title" content="{data["post"]["title"]}" />',
]
```

The callable receives the loader's return value as its argument and must return a string or list of strings.

### XSS safety

Dynamic HEAD values are automatically sanitised:

- Angle brackets (`<`, `>`) inside `<title>` text are escaped
- Event handler attributes (`onclick`, `onerror`, etc.) are stripped
- `javascript:` and `vbscript:` URLs in `href`/`src` attributes are removed

This protects against XSS when interpolating user-provided data into head elements. You should still escape user input as a best practice.

## The `<Head>` component

Use the `<Head>` component from `pyxle/client` in your JSX section:

```jsx
import { Head } from 'pyxle/client';

export default function Page({ data }) {
  return (
    <>
      <Head>
        <title>{data.title}</title>
        <meta name="robots" content="noindex" />
      </Head>
      <h1>{data.title}</h1>
    </>
  );
}
```

The `<Head>` component:

- Renders nothing in the DOM (`null`)
- During SSR, extracts its children and registers them as head elements
- Works in any component, including nested ones

## Deduplication

When multiple sources define the same head element, Pyxle deduplicates them. Later sources override earlier ones.

### Precedence order (lowest to highest)

1. Layout `<Head>` blocks
2. Page `HEAD` variable
3. Page `<Head>` blocks

### Deduplication rules

| Element | Deduplicated by |
|---------|----------------|
| `<title>` | Tag name (only one title allowed) |
| `<meta name="X">` | The `name` attribute |
| `<meta property="X">` | The `property` attribute |
| `<meta charset>` | Always one charset |
| `<link rel="canonical">` | Only one canonical |
| `<link rel="X" href="Y">` | `rel` + `href` combination |
| `<script src="X">` | The `src` attribute |
| Elements with `data-head-key="X"` | The key value |
| Everything else | Not deduplicated (all instances kept) |

### Example

```python
# Layout HEAD (lowest priority)
HEAD = '<title>My Site</title>'

# Page HEAD (overrides layout)
HEAD = '<title>About - My Site</title>'
```

Result: `<title>About - My Site</title>` (page wins).

### Manual deduplication keys

Use `data-head-key` to control deduplication for custom elements:

```python
HEAD = '<script src="/analytics.js" data-head-key="analytics"></script>'
```

If a layout and a page both define an element with the same `data-head-key`, the higher-priority source wins.

## Default title

If no `<title>` element is provided by any source, Pyxle inserts a default:

```html
<title>Pyxle</title>
```

## Next steps

- Add third-party scripts: [Client Components](client-components.md)
- Build JSON APIs: [API Routes](api-routes.md)
