## Frontend (Nestipy Web)

This project includes a Python-based frontend in `app/` plus a Vite scaffold in `web/`.

Shared UI state lives in `app/store.py` so layouts and pages can import a single source for:
- `ThemeContext` (typed `create_context`)
- `use_app_store` (typed store selector wrapper)

Build + run both backend and frontend:

```bash
nestipy start --dev --web --web-args "--vite --install"
```

Vite proxy defaults to `http://127.0.0.1:8000`. Override with:

```bash
export NESTIPY_WEB_PROXY=http://127.0.0.1:8001
```

Regenerate typed action client + Python types (optional):

```bash
nestipy run web:actions --spec http://127.0.0.1:8000/_actions/schema \
  --output web/src/actions.client.ts \
  --actions-types app/_generated/actions_types.py
```

Enable RouterSpec for typed HTTP client + Python types:

```bash
export NESTIPY_ROUTER_SPEC=1
```

Then generate the typed client:

```bash
nestipy run web:codegen --spec http://127.0.0.1:8000/_router/spec \
  --lang ts \
  --output web/src/api/client.ts \
  --router-types app/_generated/api_types.py
```

Tip: auto-refresh types in dev by passing `--actions --actions-types app/_generated/actions_types.py --router-types app/_generated/api_types.py` to `nestipy start --dev --web --web-args "..."`.

{{ ssr_block }}
