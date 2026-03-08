# Dynamic Head Component Implementation

## Overview

Implemented Next.js-style dynamic `<Head>` component support in Pyxle, allowing JSX expressions and props to be evaluated at runtime during SSR instead of being extracted as static strings at compile time.

## Changes Made

### 1. Created React Runtime Components

**Location:** `pyxle/client/`

Created real React components that work like Next.js:
- `Head.jsx` - Document head management with dynamic content support
- `Script.jsx` - Optimized script loading (placeholder)
- `Image.jsx` - Optimized image component (placeholder)
- `ClientOnly.jsx` - Client-only rendering wrapper
- `index.js` - Main export file for all client components

**Key Innovation:** The `Head` component registers itself with a global registry during SSR:

```javascript
// Server-side: Extract head elements and register them
if (typeof window === 'undefined') {
  if (typeof globalThis.__PYXLE_HEAD_REGISTRY__ !== 'undefined') {
    const headMarkup = renderToStaticMarkup(<>{children}</>);
    globalThis.__PYXLE_HEAD_REGISTRY__.register(headMarkup);
  }
}
```

### 2. Updated SSR Runtime

**File:** `pyxle/ssr/render_component.mjs`

Added head registry to extract `<Head>` content from rendered React tree:

```javascript
const headRegistry = createHeadRegistry();
globalThis.__PYXLE_HEAD_REGISTRY__ = headRegistry;

const element = React.createElement(Component, props);
const html = ReactDOMServer.renderToString(element);
const headElements = headRegistry.list();

process.stdout.write(JSON.stringify({ ok: true, html, styles, headElements }));
```

### 3. Updated Python SSR Renderer

**File:** `pyxle/ssr/renderer.py`

- Added `head_elements` field to `RenderResult` dataclass
- Added `_parse_head_elements()` function to parse extracted head from SSR runtime
- SSR now returns both rendered HTML and extracted head elements

### 4. Updated SSR View

**File:** `pyxle/ssr/view.py`

Modified `_create_page_artifacts()` to merge runtime-extracted head elements with static head blocks:

```python
render_result = await renderer.render(page.client_module_path, component_props)

# Convert runtime-extracted head elements (from <Head> components) to blocks
runtime_head_blocks = list(render_result.head_elements)

merged_head_elements = merge_head_elements(
    head_variable=head_elements,
    head_jsx_blocks=page.head_jsx_blocks + tuple(runtime_head_blocks),
    layout_head_jsx_blocks=layout_head_jsx_blocks,
)
```

### 5. Updated Client Files Generator

**File:** `pyxle/devserver/client_files.py`

Updated `_render_head_component()` to generate the new dynamic Head component with SSR registry support.

## How It Works

### Compile Time (Previous Behavior)
1. Babel extracts `<Head>` blocks as static strings
2. Stored in page metadata
3. Merged during SSR without evaluating expressions

### Runtime (New Behavior)
1. `<Head>` component imports from `pyxle/client`
2. Page component rendered by React during SSR
3. `Head` component's children evaluated with real props/data
4. `Head` registers rendered markup in global registry
5. Python SSR extracts head elements from registry
6. Merged with static head blocks (backward compatible)

### Example Usage

```jsx
import { Head } from 'pyxle/client';

export default function MyPage({ hero, meta }) {
  return (
    <>
      <Head>
        <title>{hero.title}</title>
        <meta name="description" content={meta.description} />
        <meta property="og:title" content={hero.title} />
      </Head>
      
      <div>
        <h1>{hero.title}</h1>
      </div>
    </>
  );
}
```

**Result:** The `{hero.title}` and `{meta.description}` expressions are evaluated during SSR with actual loader data, producing dynamic head content.

## Backward Compatibility

✅ Static `HEAD` variables still work
✅ Legacy compile-time `<Head>` blocks still extracted
✅ Both old and new approaches can coexist
✅ Deduplication works across all sources

## Benefits

1. **Dynamic Content:** JSX expressions evaluated with props/state
2. **Type Safety:** TypeScript autocomplete for props
3. **Consistency:** Same patterns as Next.js
4. **Flexibility:** Can use any JavaScript logic in head content
5. **No Breaking Changes:** Existing code continues to work

## Testing Status

- ✅ All 436 SSR tests pass
- ✅ Head merger tests pass
- ✅ Renderer tests pass
- ✅ Integration tests pass
- ⏳ Live testing in progress (server interruption issues)

## Known Issues

1. Client-side head updates not yet implemented (marked as future phase)
2. Need comprehensive integration tests for dynamic head scenarios
3. Server keeps getting interrupted during manual testing

## Next Steps

1. Complete live testing with dev server
2. Add integration tests for dynamic head with loader data
3. Implement client-side head updates for SPA navigation
4. Add documentation and examples
5. Consider implementing Script/Image components similarly

## Files Modified

- `pyxle/client/Head.jsx` (new)
- `pyxle/client/Script.jsx` (new)
- `pyxle/client/Image.jsx` (new)
- `pyxle/client/ClientOnly.jsx` (new)
- `pyxle/client/index.js` (new)
- `pyxle/ssr/render_component.mjs`
- `pyxle/ssr/renderer.py`
- `pyxle/ssr/view.py`
- `pyxle/devserver/client_files.py`
- `tests/ssr/test_dynamic_head.py` (new)

## Architecture Decision

Chose **Hybrid Approach** (Option C):
- Keep existing head merger infrastructure
- Add runtime extraction via React rendering
- Feed runtime-extracted head into existing merger
- Best of both worlds: backward compatible + new functionality
