# SSR Pipeline

This document explains how Pyxle renders pages on the server. Understanding the SSR pipeline is useful for debugging render issues and optimising performance.

## Overview

When a request hits a page route, Pyxle:

1. **Resolves the route** -- matches the URL to a `.pyx` file
2. **Imports the server module** -- the compiled Python code from the `@server` section
3. **Runs the loader** -- executes the `@server` function with the request
4. **Resolves HEAD elements** -- evaluates the `HEAD` variable (static or dynamic)
5. **Renders the component** -- runs React server-side rendering via Node.js
6. **Merges head elements** -- deduplicates and sanitises head elements from all sources
7. **Assembles the document** -- builds the HTML document with hydration scripts
8. **Streams the response** -- sends the HTML to the client

## Component rendering

The React component is rendered server-side using Node.js. Pyxle supports two rendering modes:

### Subprocess mode (default when workers = 0)

Each render spawns a new Node.js process:

1. esbuild bundles the component and its imports into a single file
2. Node.js executes the bundle with `renderToString` from `react-dom/server`
3. The rendered HTML and any extracted head elements are returned as JSON
4. The subprocess exits

This mode is simple but has startup overhead (~200-400ms per request).

### Worker pool mode (default: 1 worker)

Persistent Node.js processes eliminate startup cost:

1. On server start, Pyxle launches N worker processes
2. Workers stay running, communicating via stdin/stdout with newline-delimited JSON
3. Each render sends a request to an available worker
4. The worker bundles the component with esbuild, renders it, and returns the result
5. Latency drops to ~30-80ms (esbuild bundling only)

Configure workers:

```bash
pyxle dev --ssr-workers 4     # 4 persistent workers
pyxle dev --ssr-workers 0     # subprocess mode (no persistent workers)
```

## Head element pipeline

Head elements come from three sources, listed in order of increasing priority:

1. **Layout `<Head>` blocks** -- from `layout.pyx` files up the directory tree
2. **Page `HEAD` variable** -- from the Python section of the page's `.pyx` file
3. **Page `<Head>` blocks** -- from `<Head>` components in the page's JSX

The merge process:

1. All sources are split into individual elements using `HeadElementSplitter`
2. Each element is sanitised (event handlers stripped, title content escaped, dangerous URLs removed)
3. Elements are deduplicated by tag-specific keys (title by tag name, meta by name/property, etc.)
4. Higher-priority sources override lower-priority ones for duplicate keys
5. Non-deduplicatable elements (inline scripts, custom tags) are all included

## Document assembly

The final HTML document is structured as:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <!-- Vite client (dev mode) or production JS/CSS links -->
    <!-- Global styles (inlined) -->
    <!-- Merged head elements -->
  </head>
  <body>
    <div id="root">
      <!-- Server-rendered HTML -->
    </div>
    <script id="__PYXLE_PROPS__" type="application/json">
      <!-- Serialised props for hydration -->
    </script>
    <script>window.__PYXLE_PAGE_PATH__ = "/page-path";</script>
    <script type="module" src="..."></script>
  </body>
</html>
```

In dev mode, the document includes the Vite client script and React Refresh preamble for hot module replacement.

## Streaming

For production builds with a manifest, Pyxle uses `StreamingResponse` to send the document in chunks:

1. The HTML prefix (up to `<div id="root">`) is sent immediately
2. The server-rendered body HTML follows
3. The suffix (hydration scripts and closing tags) completes the stream

This allows the browser to start parsing and rendering before the full document is ready.

## Error handling

Errors at each stage are handled differently:

| Stage | Error type | Behaviour |
|-------|-----------|-----------|
| Loader | `LoaderError` | Renders nearest `error.pyx` with error context |
| Loader | Other exceptions | Renders `error.pyx` or default error document |
| HEAD evaluation | `HeadEvaluationError` | Renders `error.pyx` or default error document |
| Component render | `ComponentRenderError` | Renders `error.pyx` or default error document |

In dev mode, the error overlay shows the error with breadcrumbs indicating which stage failed.

## Client-side navigation

When navigating between pages client-side, Pyxle uses a JSON endpoint instead of full HTML:

```
GET /page-path?__pyxle_nav=1
```

This returns:

```json
{
  "ok": true,
  "routePath": "/page-path",
  "props": { "data": { ... } },
  "headMarkup": "..."
}
```

The client runtime swaps the component props and updates the document head without a full page reload.

## Performance tips

- **Use worker pool mode** (`--ssr-workers N`) for production. Start with N = number of CPU cores.
- **Keep loader functions fast.** The loader runs on every request -- cache expensive calls.
- **Avoid heavy imports in the Python section.** Imports are loaded every time the module is hot-reloaded in dev mode.
- **Minimise HEAD callable complexity.** Dynamic HEAD functions run synchronously on the main thread.
