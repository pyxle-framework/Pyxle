# Framework Primitives

Pyxle ships framework-owned components inspired by Next.js that feel native to Python-first development.

## Quick reference

| Primitive | Purpose | Import |
|-----------|---------|--------|
| `<Link>` | Client-side navigation | `from pyxle/client` |
| `<Script>` | Load external scripts with strategies | `from pyxle/client` |
| `<Image>` | Responsive images + CLS prevention | `from pyxle/client` |
| `<Head>` | JSX-based metadata (alongside `HEAD` variable) | `from pyxle/client` |
| `<ClientOnly>` | Skip SSR for browser-only components | `from pyxle/client` |
| `navigate()` | Imperative navigation | `from pyxle/client` |
| `prefetch()` | Warm navigation cache | `from pyxle/client` |

---

## `<Script />`

Load external scripts with explicit execution timing.

### API

```jsx
import { Script } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <Script src="https://example.com/sdk.js" strategy="afterInteractive" />
      <h1>My App</h1>
    </>
  );
}
```

### Props

- **`src`** (required): URL of the external script
- **`strategy`** (default: `"afterInteractive"`):
  - `"beforeInteractive"` – Inject inline in `<head>` before page render
  - `"afterInteractive"` – Load after hydration (safe for analytics, ads)
  - `"lazyOnload"` – Load on idle via `requestIdleCallback`
- **`async`** (default: `false`) – Add `async` attribute
- **`defer`** (default: `false`) – Add `defer` attribute
- **`module`** (default: `false`) – Add `type="module"`
- **`onLoad`** – Callback when script loads
- **`onError`** – Callback if script fails

### Examples

**Analytics (after hydration):**
```jsx
<Script src="https://analytics.example.com/tracker.js" strategy="afterInteractive" />
```

**Before page render (critical):**
```jsx
<Script src="https://critical-lib.js" strategy="beforeInteractive" />
```

**Idle time (lazy):**
```jsx
<Script src="https://optional.js" strategy="lazyOnload" />
```

### Compare with Next.js

`<Script />` works identically to `next/script` with the same strategy semantics. Pyxle doesn't yet support `src` attribute removal or inline scripts, but follows the same mental model.

---

## `<Image />`

Responsive images that prevent layout shift (CLS).

### API

```jsx
import { Image } from 'pyxle/client';

export default function Page() {
  return (
    <Image src="/hero.png" width={800} height={400} alt="Hero" />
  );
}
```

### Props

- **`src`** (required): Image URL
- **`width`** (required): Intrinsic width (used for aspect ratio)
- **`height`** (required): Intrinsic height (used for aspect ratio)
- **`alt`** (required): Alt text for accessibility
- **`priority`** (default: `false`) – Disable lazy loading for above-fold images
- **`lazy`** (default: `true`) – Enable native `loading="lazy"`

### How it works

1. Generates an aspect-ratio CSS container so the image space is reserved before load
2. Applies `loading="lazy"` by default
3. Sets `loading="eager"` if `priority={true}` (for LCP images)
4. Falls back to `IntersectionObserver` if native lazy loading is unavailable

### Examples

**Above-the-fold hero (no lazy):**
```jsx
<Image src="/hero.png" width={1200} height={600} alt="Hero" priority />
```

**Below-the-fold gallery (lazy):**
```jsx
<Image src="/gallery/img-1.png" width={400} height={300} alt="Gallery image" />
```

### Compare with Next.js

Similar to `next/image` in terms of props, but Pyxle does not (yet) support:
- Automatic AVIF/WebP conversion
- Blur placeholder
- Size guessing

These can be added post-MVP as CDN integration.

---

## `<Head />`

Declare metadata inside JSX (alongside the compiler `HEAD` variable).

### API

```jsx
import { Head } from 'pyxle/client';

export default function Page({ data }) {
  return (
    <>
      <Head>
        <title>{data.title} • My App</title>
        <meta name="description" content={data.description} />
        <meta property="og:image" content={data.ogImage} />
      </Head>
      <h1>{data.title}</h1>
    </>
  );
}
```

### Merge rules

- Layout → Template → Page (stacked deterministically)
- `<title>` overrides previous (last wins)
- `<meta name="..." >` deduplicates by `name` attribute
- `<link rel="..." >` deduplicates by `rel` attribute
- Multiple `<Head>` blocks in same component are merged

### Comparison with `HEAD` variable

Both work; use whichever feels natural:

**Compiler-driven (static):**
```python
HEAD = """
<title>Home</title>
<meta name="description" content="..." />
"""
```

**JSX-based (dynamic):**
```jsx
<Head>
  <title>{computeTitle(data)}</title>
  <meta name="description" content={data.description} />
</Head>
```

### Best practice

- Use `HEAD` variable for static site-wide metadata
- Use `<Head>` component for dynamic, page-specific metadata
- Avoid scripts inside `<Head>`; use `<Script />` instead

---

## `<ClientOnly />`

Opt out of SSR for specific components.

### API

```jsx
import { ClientOnly } from 'pyxle/client';

export default function Page() {
  return (
    <>
      <h1>My App</h1>
      <ClientOnly fallback={<Skeleton />}>
        <InteractiveMap />
      </ClientOnly>
    </>
  );
}
```

### Props

- **`children`** (required): Component to render only on client
- **`fallback`** (optional): Placeholder during SSR (defaults to empty div)

### Use cases

- Maps, charts, or other third-party widgets requiring browser APIs
- Components using `localStorage` or `sessionStorage`
- Analytics dashboards
- Code editors

### How it works

1. During SSR, renders the `fallback` (or empty div)
2. On client mount, renders `children` after hydration
3. No hydration mismatch warnings

### Example: Map library

```jsx
import { ClientOnly } from 'pyxle/client';
import dynamic from 'react'; // or your map library

const MapComponent = () => <div id="map" />;

export default function Page() {
  return (
    <ClientOnly fallback={<div>Loading map...</div>}>
      <MapComponent />
    </ClientOnly>
  );
}
```

---

## `<Link />` (Already implemented)

SPA-aware anchor with prefetching.

### API

```jsx
import { Link } from 'pyxle/client';

<Link href="/about" prefetch="hover">
  About Us
</Link>
```

### Props

- **`href`** (required): Route or URL
- **`prefetch`** (default: `true`) – Prefetch on hover/viewport entry
- **`replace`** (default: `false`) – Replace history instead of push
- **`scroll`** (default: `true`) – Scroll to top on navigation

See [Client Navigation](../routing/client-navigation.md) for full details.

---

## Metadata / Head System (Already implemented)

Pyxle provides a compiler-driven head metadata system:

- `HEAD` variable in `.pyx` files (static or callable)
- Merged with route layout hierarchy
- SSR template injects into document head
- Navigation payloads include head diffs

See [Head Management](head-management.md) for full details.

---

## Future primitives (Post-MVP)

- `<Form>` – Type-safe server actions
- `<Suspense>` – Streaming SSR boundaries
- `useRouter()` – Imperative route inspection
- `useNavigation()` – Navigation state hook

---

**Navigation:** [← Previous](./pyxle-client.md) | [Next →](../deployment/deployment.md)

