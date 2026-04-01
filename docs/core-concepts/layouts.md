# Layouts

Layouts wrap pages in shared UI -- navigation bars, sidebars, footers, and other elements that persist across page navigations.

## Creating a layout

Add a `layout.pyx` file to any directory inside `pages/`. It wraps all pages in that directory and its subdirectories:

```
pages/
  layout.pyx         # Root layout -- wraps ALL pages
  index.pyx
  about.pyx
  dashboard/
    layout.pyx       # Dashboard layout -- wraps only dashboard pages
    index.pyx
    settings.pyx
```

A layout is a React component that receives `children`:

```jsx
// pages/layout.pyx
export default function RootLayout({ children }) {
  return (
    <div className="min-h-screen">
      <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
      </nav>
      <main>{children}</main>
      <footer>Built with Pyxle</footer>
    </div>
  );
}
```

### Slots

Layouts can export a `slots` object and a `createSlots` function for passing additional content from pages:

```jsx
// pages/layout.pyx
export const slots = {};
export const createSlots = () => slots;

export default function RootLayout({ children }) {
  return <div>{children}</div>;
}
```

## Nesting layouts

Layouts nest automatically. If both `pages/layout.pyx` and `pages/dashboard/layout.pyx` exist, a page at `pages/dashboard/settings.pyx` is wrapped by both:

```
RootLayout
  DashboardLayout
    SettingsPage
```

Inner layouts are rendered inside outer layouts. The root layout is always the outermost wrapper.

## Templates

A `template.pyx` file works like a layout but **resets component state on every navigation**. Use templates when you want a fresh React component tree for each page in the group:

```
pages/
  layout.pyx           # Persists across navigation
  auth/
    template.pyx       # Resets state on navigation between auth pages
    login.pyx
    register.pyx
```

Templates are useful for authentication flows, wizards, or any section where you want form state and scroll position to reset when moving between pages.

## Layout vs template

| Behaviour | `layout.pyx` | `template.pyx` |
|-----------|-------------|----------------|
| Wraps child pages | Yes | Yes |
| Preserves state on navigation | Yes | No (remounts) |
| Can nest | Yes | Yes |
| Typical use | Nav bars, sidebars | Auth flows, wizards |

## Layouts are JSX-only

Layout files typically contain only JSX -- no `@server` loader or `@action` functions. If you need shared data across pages, fetch it in each page's loader or use a shared Python utility.

## How it works

When Pyxle compiles your pages, it:

1. Walks up from each page to the root, collecting `layout.pyx` and `template.pyx` files
2. Generates a composed wrapper module that nests them in the correct order
3. At render time, the page component is passed as `children` to the innermost layout

## Next steps

- Style your layouts with Tailwind: [Styling](../guides/styling.md)
- Add navigation between pages: [Client Components](../guides/client-components.md)
