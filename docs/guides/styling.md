# Styling

Pyxle ships with Tailwind CSS out of the box. You can also use global CSS files, inline styles, or any CSS-in-JS solution that works with React.

## Tailwind CSS

Every scaffolded project includes Tailwind CSS pre-configured.

### How it works

1. `pages/styles/tailwind.css` is the Tailwind input file containing `@tailwind` directives
2. Tailwind compiles it to `public/styles/tailwind.css`
3. The compiled CSS is linked in your page's `HEAD` variable

### Development workflow

The `pyxle dev` command auto-starts a Tailwind watcher if it detects a Tailwind config file (`tailwind.config.cjs`, `tailwind.config.js`, etc.). You can disable this with `--no-tailwind`:

```bash
pyxle dev              # Tailwind watcher starts automatically
pyxle dev --no-tailwind  # Skip Tailwind watcher
```

Alternatively, run the Tailwind watcher in a separate terminal:

```bash
npm run dev:css
```

### Production builds

`pyxle build` runs `npm run build`, which triggers `npm run build:css` before the Vite bundle. The minified CSS ends up in your production output.

### Configuration

The scaffold generates a `tailwind.config.cjs` that scans `.pyx` and `.jsx` files:

```javascript
module.exports = {
  content: ['./pages/**/*.{pyx,jsx,js,tsx,ts}'],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### Dark mode

The scaffold includes a theme toggle script that reads from `localStorage` and respects `prefers-color-scheme`. Toggle the `dark` class on `<html>` to switch themes:

```jsx
function toggleTheme() {
  document.documentElement.classList.toggle('dark');
}
```

Use Tailwind's `dark:` modifier for dark-mode styles:

```jsx
<div className="bg-white dark:bg-slate-900 text-black dark:text-white">
  Content
</div>
```

## Global stylesheets

Register CSS files that should be inlined on every page:

```json
{
  "styling": {
    "globalStyles": [
      "styles/reset.css",
      "styles/typography.css"
    ]
  }
}
```

Paths are relative to the project root. Global styles are loaded in order and inlined into the SSR HTML as `<style>` tags, so they work even before JavaScript loads.

## Global scripts

Register JavaScript files loaded on every page:

```json
{
  "styling": {
    "globalScripts": [
      "scripts/analytics.js"
    ]
  }
}
```

## Linking a stylesheet in HEAD

For external or compiled stylesheets, link them in the `HEAD` variable:

```python
HEAD = '<link rel="stylesheet" href="/styles/tailwind.css" />'
```

Or in a layout's JSX:

```jsx
import { Head } from 'pyxle/client';

export default function Layout({ children }) {
  return (
    <>
      <Head>
        <link rel="stylesheet" href="/styles/tailwind.css" />
      </Head>
      {children}
    </>
  );
}
```

## CSS-in-JS

Any CSS-in-JS library that works with React 18 and SSR should work with Pyxle. Install it via npm and import it in your JSX section.

## Next steps

- Manage document head elements: [Head Management](head-management.md)
- Add scripts with loading strategies: [Client Components](client-components.md)
