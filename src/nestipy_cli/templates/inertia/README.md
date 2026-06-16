# nestipy_app

A fullstack [Nestipy](https://github.com/nestipy/nestipy) + [Inertia.js](https://inertiajs.com) app
(Python backend + a Vite frontend).

## Run (backend + frontend together)

```bash
uv sync
nestipy start --dev --web
```

`--web` starts the Inertia frontend dev server (`npm run dev` in `./inertia`,
installing deps first if needed) alongside the backend, then open
http://localhost:8000.

## Run them separately

```bash
# terminal 1 — backend
nestipy start --dev

# terminal 2 — frontend
cd inertia
npm install
npm run dev
```

The backend serves the Inertia root template (`views/index.html`) and renders pages from
`src/app_controller.py`; the Vite dev server provides the frontend modules referenced
through `inertiaHead()` / `inertiaBody()`.

## Production build

```bash
cd inertia
npm run build      # outputs inertia/dist
```

## Pages

React pages live in `inertia/src/Pages`. Controllers render them by name:

```python
return await res.inertia.render("Index", {"message": "hello"})
```

Prop helpers: `optional(fn)` (sent only on partial reload), `defer(fn)` (fetched after first
paint), `merge(fn)` / `deep_merge(fn)` (merge instead of overwrite).
