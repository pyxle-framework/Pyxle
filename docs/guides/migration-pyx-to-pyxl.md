# Migrating from `.pyx` to `.pyxl`

Pyxle's file extension has changed from `.pyx` to `.pyxl`. This guide explains why and how to update your project.

## Why the change?

The `.pyx` extension is already used by [Cython](https://cython.org/), a well-established Python compiler. This collision caused real problems:

- **GitHub misclassification** — GitHub's linguist identifies `.pyx` files as Cython, causing repository language stats to show "Cython" instead of "Pyxle."
- **IDE conflicts** — VS Code, JetBrains, and other editors default to Cython syntax highlighting when opening `.pyx` files, requiring manual overrides.
- **Search confusion** — Searching for ".pyx files" returns Cython documentation and tutorials, making Pyxle harder to discover.
- **Tooling friction** — Linters, formatters, and CI tools with Cython support may interfere with Pyxle files.

The new `.pyxl` extension is unique, maps clearly to the "Pyxle" name, and eliminates all of these issues.

## What changed?

Only the file extension. The file format, syntax, and behavior are completely identical:

| Before | After |
|--------|-------|
| `pages/index.pyx` | `pages/index.pyxl` |
| `pages/layout.pyx` | `pages/layout.pyxl` |
| `pages/not-found.pyx` | `pages/not-found.pyxl` |
| `pages/error.pyx` | `pages/error.pyxl` |

Everything inside the files — Python server blocks, JSX client code, `@server` loaders, `@action` mutations — works exactly the same.

## How to migrate

### 1. Rename all `.pyx` files to `.pyxl`

```bash
# From your project root:
find pages/ -name '*.pyx' -exec bash -c 'mv "$1" "${1%.pyx}.pyxl"' _ {} \;
```

### 2. Update imports between pages

If any of your `.pyxl` files import from other pages, update the extension in the import path:

```jsx
// Before
import { useTheme } from './layout.pyx';

// After
import { useTheme } from './layout.pyxl';
```

### 3. Update the VS Code extension

If you're using the Pyxle VS Code extension (`pyxle-langkit`), update to the latest version. The new version registers `.pyxl` as the file extension for syntax highlighting, diagnostics, and formatting.

### 4. Verify

Run `pyxle check` to confirm all files are recognized:

```bash
pyxle check
```

You should see output like:

```
Checked 5 .pyxl file(s) in my-project/
```

## Timeline

This change was made before Pyxle's public launch, so no existing user projects are affected. If you cloned an early version of the framework or followed pre-release tutorials, this guide covers the one-time migration needed.
