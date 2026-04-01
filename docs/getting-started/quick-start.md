# Quick Start

Create a working Pyxle app in under 5 minutes.

## 1. Scaffold a new project

```bash
pyxle init my-app
```

This creates a `my-app/` directory with a complete starter project.

## 2. Install dependencies

```bash
cd my-app
pyxle install
```

This runs both `pip install -r requirements.txt` and `npm install`. You can also run them separately:

```bash
pip install -r requirements.txt
npm install
```

## 3. Build Tailwind CSS

In a separate terminal, start the Tailwind watcher:

```bash
npm run dev:css
```

This compiles `pages/styles/tailwind.css` into `public/styles/tailwind.css` and watches for changes. The dev server also auto-starts Tailwind if it detects a config file, so this step is optional if you use `pyxle dev` with the `--tailwind` flag (enabled by default).

## 4. Start the dev server

```bash
pyxle dev
```

Open [http://localhost:8000](http://localhost:8000) in your browser. You should see the Pyxle landing page with a hero section, feature cards, and a dark mode toggle.

## What just happened?

When you ran `pyxle dev`, the framework:

1. **Compiled** `pages/index.pyx` -- split the Python server code from the React JSX
2. **Started Vite** -- the JavaScript bundler that serves your React components with hot reload
3. **Started Starlette** -- the Python ASGI server that handles routing, SSR, and API requests
4. **Ran the `@server` loader** -- fetched data on the server and passed it as props to React
5. **Rendered HTML on the server** -- sent fully-rendered HTML to the browser (SSR)
6. **Hydrated on the client** -- React took over the server-rendered HTML for interactivity

## 5. Make a change

Open `pages/index.pyx` in your editor. Find the `title` value inside the `load_home` function and change it:

```python
@server
async def load_home(request):
    return {
        "hero": {
            "title": "Hello from Pyxle!",
            # ...
        },
    }
```

Save the file. The browser reloads automatically with your updated title.

## 6. Check your routes

```bash
pyxle routes
```

This prints the route table derived from your `pages/` directory:

```
Route          File                  Loader
/              pages/index.pyx       load_home
/api/pulse     pages/api/pulse.py    --
```

## 7. Validate your project

```bash
pyxle check
```

This validates `.pyx` syntax, checks your config file, and reports any issues.

## Next steps

- Understand what each file does: [Project Structure](project-structure.md)
- Learn the `.pyx` file format: [`.pyx` Files](../core-concepts/pyx-files.md)
- Add a new page with data loading: [Data Loading](../core-concepts/data-loading.md)
