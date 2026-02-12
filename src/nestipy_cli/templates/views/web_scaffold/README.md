
## Frontend (Nestipy Web)

This project includes a Python-based frontend in `app/` plus a Vite scaffold in `web/`.

Build + run both backend and frontend:

```bash
nestipy start --dev --web --web-args "--vite --install"
```

Vite proxy defaults to `http://127.0.0.1:8000`. Override with:

```bash
export NESTIPY_WEB_PROXY=http://127.0.0.1:8001
```

Regenerate typed action client (optional):

```bash
nestipy run web:actions --spec http://127.0.0.1:8000/_actions/schema --output web/src/actions.client.ts
```

Enable RouterSpec for typed HTTP client:

```bash
export NESTIPY_ROUTER_SPEC=1
```

Then generate the typed client:

```bash
nestipy run web:build --spec http://127.0.0.1:8000/_router/spec --lang ts --output web/src/api/client.ts
```
