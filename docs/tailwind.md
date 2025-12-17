# Tailwind CSS Integration Guide

Every `pyxle init` project now ships with Tailwind and PostCSS preconfigured:

- `tailwind.config.cjs` watches both your source `.pyx` files (mixed Python + JSX) and the transpiled `.pyxle-build/client/pages/**/*.jsx` output so production builds never miss a class.
- `postcss.config.cjs` registers the Tailwind + Autoprefixer plugins for Vite.
- `pages/styles/tailwind.css` contains the `@tailwind` directives. Run `npm run dev:css` (or rely on `pyxle build`, which runs `npm run build` and thus `build:css`) to keep `/public/styles/tailwind.css` up to date; the scaffold links it directly from `pages/index.pyx`, so SSR responses never depend on JavaScript to load styles.

The steps below focus on customizing the defaults.

## 1. Extend the theme or content globs

Update `tailwind.config.cjs` to match your project structure. The scaffold uses `module.exports` to stay compatible with Node's CommonJS loader even though `package.json` sets `"type": "module"`.

```js
/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './pages/**/*.{pyx,js,jsx,ts,tsx}',
        './.pyxle-build/client/pages/**/*.{js,jsx,ts,tsx}',
    ],
    theme: {
        extend: {
            colors: {
                brand: {
                    DEFAULT: '#0f172a',
                    accent: '#38bdf8',
                },
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
    ],
};
```

Restart `pyxle dev` whenever you change the config so Vite reloads the Tailwind process.

## 2. Layer in additional base styles

Add custom utilities or components inside `pages/styles/tailwind.css` using Tailwind's layering primitives:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
    html {
        scroll-behavior: smooth;
    }

    ::selection {
        @apply bg-cyan-200 text-slate-900;
    }
}
```

Since the layout imports this file, every page immediately receives the new styles. Prefer a per-page stylesheet? Create another `.css` file next to the page and import it from the JavaScript block—Vite handles the bundling.

## 3. Build or watch the stylesheet

Every scaffold ships with two npm scripts so you can regenerate `/public/styles/tailwind.css`
without wiring extra tooling:

```jsonc
{
    "scripts": {
        "dev:css": "tailwindcss -i ./pages/styles/tailwind.css -o ./public/styles/tailwind.css --watch",
        "build:css": "tailwindcss -i ./pages/styles/tailwind.css -o ./public/styles/tailwind.css --minify"
    }
}
```

- Run `npm run dev:css` in a second terminal while `pyxle dev` is running so edits to
    `.pyx` files or the Tailwind entry sheet immediately refresh the linked CSS file.
- Run `npm run build:css` when you need a standalone asset (for example, CI jobs that
    only bundle static marketing pages). `pyxle build` already calls `npm run build`
    automatically, so the Tailwind bundle is regenerated before every production build.

Because `/styles/tailwind.css` is linked from the shared head, browsers download it during
SSR even when JavaScript is disabled.

## 4. Troubleshooting

- **Classes not applying?** Ensure the class string lives inside one of the `content` paths (for example, `.pyx` or `.jsx`). Tailwind's JIT won't emit styles for files outside those globs.
- **New plugin not loading?** Install it with `npm install -D` and add `require('plugin-name')` to the `plugins` array in `tailwind.config.cjs`.
- **Need per-route themes?** Import a route-specific stylesheet inside that page's JavaScript block. All CSS files under `pages/` are copied to `.pyxle-build/client/pages/` so Vite can resolve them.
