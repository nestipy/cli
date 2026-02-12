import os.path
import re

import autoflake
import autopep8
import isort

from .templates.generator import TemplateGenerator


class NestipyCliHandler:
    generator: TemplateGenerator

    def __init__(self):
        self.generator = TemplateGenerator()

    def create_project(self, name, frontend: bool = False) -> bool:
        destination = os.path.join(os.getcwd(), name)
        if name == ".":
            destination = os.getcwd()
        if os.path.exists(destination) and name != ".":
            return False
        self.generator.copy_project(destination)
        if frontend:
            project_name = os.path.basename(destination.rstrip(os.sep))
            if not project_name:
                project_name = "nestipy-app"
            self._add_frontend_scaffold(destination, project_name=project_name)
        return True

    def _write_file(self, path: str, content: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def _append_readme(self, destination: str, content: str) -> None:
        readme_path = os.path.join(destination, "README.md")
        if not os.path.exists(readme_path):
            return
        with open(readme_path, "a", encoding="utf-8") as handle:
            handle.write(content)

    def _add_frontend_scaffold(self, destination: str, project_name: str) -> None:
        app_dir = os.path.join(destination, "app")
        web_dir = os.path.join(destination, "web")

        self._write_file(
            os.path.join(app_dir, "layout.py"),
            "\n".join(
                [
                    "from nestipy.web import component, h, Slot, js, use_state, use_callback, create_context",
                    "",
                    "ThemeContext = create_context({\"theme\": \"dark\", \"toggle\": None})",
                    "",
                    "@component",
                    "def Layout():",
                    "    theme, set_theme = use_state(\"dark\")",
                    "",
                    "    def toggle_theme():",
                    "        set_theme(\"light\" if theme == \"dark\" else \"dark\")",
                    "",
                    "    toggle_handler = use_callback(toggle_theme, deps=[theme])",
                    "    return h(",
                    "        ThemeContext.Provider,",
                    "        value=js(\"{ theme, toggle: toggle_handler }\"),",
                    "        h.header(",
                    "            h.h1(\"Nestipy Web\"),",
                    "            h.p(js(\"`Theme: ${theme}`\"), class_name=\"text-sm opacity-80\"),",
                    "            class_name=\"space-y-1\",",
                    "        ),",
                    "        h(Slot),",
                    "        class_name=\"min-h-screen bg-slate-950 text-white p-8 space-y-6\",",
                    "    )",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(app_dir, "page.py"),
            "\n".join(
                [
                    "from nestipy.web import (",
                    "    component,",
                    "    h,",
                    "    js,",
                    "    use_state,",
                    "    use_effect,",
                    "    use_memo,",
                    "    use_callback,",
                    "    use_context,",
                    "    external,",
                    ")",
                    "from layout import ThemeContext",
                    "",
                    "Link = external(\"react-router-dom\", \"Link\")",
                    "CreateActions = external(\"../actions.client\", \"createActions\")",
                    "ApiClient = external(\"../../api/client\", \"ApiClient\")",
                    "",
                    "actions = js(\"createActions()\")",
                    "api = js(\"new ApiClient({ baseUrl: '' })\")",
                    "",
                    "@component",
                    "def Page():",
                    "    theme = use_context(ThemeContext)",
                    "    message, set_message = use_state(\"Loading...\")",
                    "    ping, set_ping = use_state(\"Loading...\")",
                    "",
                    "    def on_action(result):",
                    "        set_message(js(\"result.ok ? result.data : 'Error'\"))",
                    "",
                    "    def on_ping(value):",
                    "        set_ping(value)",
                    "",
                    "    def load_action():",
                    "        actions.AppActions.hello({\"name\": \"Nestipy\"}).then(on_action)",
                    "",
                    "    def load_ping():",
                    "        api.ping().then(on_ping)",
                    "",
                    "    reload_action = use_callback(load_action, deps=[])",
                    "    reload_ping = use_callback(load_ping, deps=[])",
                    "",
                    "    def label():",
                    "        return f\"Action says: {message}\"",
                    "",
                    "    action_label = use_memo(label, deps=[message])",
                    "    use_effect(load_action, deps=[])",
                    "    use_effect(load_ping, deps=[])",
                    "    return h.div(",
                    "        h.nav(",
                    "            Link(\"Home\", to=\"/\"),",
                    "            Link(\"Counter\", to=\"/counter\"),",
                    "            Link(\"API\", to=\"/api\"),",
                    "            class_name=\"flex gap-4 text-sm\",",
                    "        ),",
                    "        h.h2(\"Overview\", class_name=\"text-lg font-semibold\"),",
                    "        h.p(js(\"action_label\"), class_name=\"text-sm\"),",
                    "        h.p(js(\"`API ping: ${ping}`\"), class_name=\"text-xs opacity-80\"),",
                    "        h.div(",
                    "            h.button(",
                    "                \"Reload Action\",",
                    "                on_click=js(\"reload_action\"),",
                    "                class_name=\"px-3 py-1 rounded bg-blue-600 text-white\",",
                    "            ),",
                    "            h.button(",
                    "                \"Reload API\",",
                    "                on_click=js(\"reload_ping\"),",
                    "                class_name=\"px-3 py-1 rounded bg-slate-700 text-white\",",
                    "            ),",
                    "            class_name=\"flex gap-3\",",
                    "        ),",
                    "        h.p(js(\"`Theme: ${theme.theme}`\"), class_name=\"text-xs opacity-70\"),",
                    "        class_name=\"space-y-4\",",
                    "    )",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(app_dir, "counter", "page.py"),
            "\n".join(
                [
                    "from nestipy.web import (",
                    "    component,",
                    "    h,",
                    "    js,",
                    "    use_state,",
                    "    use_memo,",
                    "    use_callback,",
                    "    use_context,",
                    "    external,",
                    ")",
                    "from layout import ThemeContext",
                    "",
                    "Link = external(\"react-router-dom\", \"Link\")",
                    "",
                    "@component",
                    "def Page():",
                    "    theme = use_context(ThemeContext)",
                    "    count, set_count = use_state(0)",
                    "",
                    "    def increment():",
                    "        set_count(count + 1)",
                    "",
                    "    def decrement():",
                    "        set_count(count - 1)",
                    "",
                    "    inc = use_callback(increment, deps=[count])",
                    "    dec = use_callback(decrement, deps=[count])",
                    "",
                    "    def label():",
                    "        return f\"Count: {count}\"",
                    "",
                    "    title = use_memo(label, deps=[count])",
                    "    return h.div(",
                    "        h.nav(",
                    "            Link(\"Home\", to=\"/\"),",
                    "            Link(\"Counter\", to=\"/counter\"),",
                    "            Link(\"API\", to=\"/api\"),",
                    "            class_name=\"flex gap-4 text-sm\",",
                    "        ),",
                    "        h.h2(\"Counter\", class_name=\"text-lg font-semibold\"),",
                    "        h.p(js(\"title\"), class_name=\"text-sm\"),",
                    "        h.div(",
                    "            h.button(",
                    "                \"+1\",",
                    "                on_click=js(\"inc\"),",
                    "                class_name=\"px-3 py-1 rounded bg-blue-600 text-white\",",
                    "            ),",
                    "            h.button(",
                    "                \"-1\",",
                    "                on_click=js(\"dec\"),",
                    "                class_name=\"px-3 py-1 rounded bg-slate-700 text-white\",",
                    "            ),",
                    "            class_name=\"flex gap-3\",",
                    "        ),",
                    "        h.p(js(\"`Theme: ${theme.theme}`\"), class_name=\"text-xs opacity-70\"),",
                    "        class_name=\"space-y-4\",",
                    "    )",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(app_dir, "api", "page.py"),
            "\n".join(
                [
                    "from nestipy.web import (",
                    "    component,",
                    "    h,",
                    "    js,",
                    "    use_state,",
                    "    use_effect,",
                    "    use_callback,",
                    "    use_context,",
                    "    external,",
                    ")",
                    "from layout import ThemeContext",
                    "",
                    "Link = external(\"react-router-dom\", \"Link\")",
                    "ApiClient = external(\"../api/client\", \"ApiClient\")",
                    "",
                    "api = js(\"new ApiClient({ baseUrl: '' })\")",
                    "",
                    "@component",
                    "def Page():",
                    "    theme = use_context(ThemeContext)",
                    "    status, set_status = use_state(\"Loading...\")",
                    "",
                    "    def on_ping(value):",
                    "        set_status(value)",
                    "",
                    "    def load():",
                    "        api.ping().then(on_ping)",
                    "",
                    "    refresh = use_callback(load, deps=[])",
                    "    use_effect(load, deps=[])",
                    "    return h.div(",
                    "        h.nav(",
                    "            Link(\"Home\", to=\"/\"),",
                    "            Link(\"Counter\", to=\"/counter\"),",
                    "            Link(\"API\", to=\"/api\"),",
                    "            class_name=\"flex gap-4 text-sm\",",
                    "        ),",
                    "        h.h2(\"Typed API\", class_name=\"text-lg font-semibold\"),",
                    "        h.p(js(\"`Ping: ${status}`\"), class_name=\"text-sm\"),",
                    "        h.button(",
                    "            \"Refresh\",",
                    "            on_click=js(\"refresh\"),",
                    "            class_name=\"px-3 py-1 rounded bg-blue-600 text-white\",",
                    "        ),",
                    "        h.p(js(\"`Theme: ${theme.theme}`\"), class_name=\"text-xs opacity-70\"),",
                    "        class_name=\"space-y-4\",",
                    "    )",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(destination, "app_actions.py"),
            "\n".join(
                [
                    "from nestipy.common import Injectable",
                    "from nestipy.web import action",
                    "",
                    "",
                    "@Injectable()",
                    "class AppActions:",
                    "    @action()",
                    "    async def hello(self, name: str = \"Nestipy\") -> str:",
                    "        return f\"Hello, {name}!\"",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(destination, "app_controller.py"),
            "\n".join(
                [
                    "from typing import Annotated",
                    "",
                    "from nestipy.common import Controller, Get",
                    "from nestipy.ioc import Inject",
                    "",
                    "from app_service import AppService",
                    "",
                    "",
                    "@Controller(\"/api\")",
                    "class AppController:",
                    "    service: Annotated[AppService, Inject()]",
                    "",
                    "    @Get(\"/ping\")",
                    "    async def ping(self) -> str:",
                    "        return \"pong\"",
                    "",
                    "    @Get(\"/message\")",
                    "    async def message(self) -> str:",
                    "        return await self.service.get()",
                    "",
                ]
            ),
        )

        app_module_path = os.path.join(destination, "app_module.py")
        self._write_file(
            app_module_path,
            "\n".join(
                [
                    "from nestipy.common import Module",
                    "from nestipy.web import ActionsModule, ActionsOption",
                    "",
                    "from app_controller import AppController",
                    "from app_service import AppService",
                    "from app_actions import AppActions",
                    "",
                    "",
                    "@Module(",
                    "    imports=[ActionsModule.for_root(ActionsOption(path=\"/_actions\"))],",
                    "    controllers=[AppController],",
                    "    providers=[AppService, AppActions],",
                    ")",
                    "class AppModule: ...",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "index.html"),
            "\n".join(
                [
                    "<!DOCTYPE html>",
                    "<html lang='en'>",
                    "  <head>",
                    "    <meta charset='UTF-8' />",
                    "    <meta name='viewport' content='width=device-width, initial-scale=1.0' />",
                    "    <title>Nestipy Web</title>",
                    "  </head>",
                    "  <body>",
                    "    <div id='root'></div>",
                    "    <script type='module' src='/src/main.tsx'></script>",
                    "  </body>",
                    "</html>",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "package.json"),
            "\n".join(
                [
                    "{",
                    f"  \"name\": \"{project_name}\",",
                    "  \"private\": true,",
                    "  \"version\": \"0.0.0\",",
                    "  \"type\": \"module\",",
                    "  \"scripts\": {",
                    "    \"dev\": \"vite\",",
                    "    \"build\": \"vite build\",",
                    "    \"preview\": \"vite preview\"",
                    "  },",
                    "  \"dependencies\": {",
                    "    \"react\": \"latest\",",
                    "    \"react-dom\": \"latest\",",
                    "    \"react-router-dom\": \"latest\"",
                    "  },",
                    "  \"devDependencies\": {",
                    "    \"@types/react\": \"latest\",",
                    "    \"@types/react-dom\": \"latest\",",
                    "    \"@vitejs/plugin-react\": \"latest\",",
                    "    \"autoprefixer\": \"latest\",",
                    "    \"postcss\": \"latest\",",
                    "    \"tailwindcss\": \"latest\",",
                    "    \"typescript\": \"latest\",",
                    "    \"vite\": \"latest\"",
                    "  }",
                    "}",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "vite.config.ts"),
            "\n".join(
                [
                    "import { defineConfig } from 'vite';",
                    "import react from '@vitejs/plugin-react';",
                    "",
                    "export default defineConfig({",
                    "  plugins: [react()],",
                    "});",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "tsconfig.json"),
            "\n".join(
                [
                    "{",
                    "  \"compilerOptions\": {",
                    "    \"target\": \"ES2020\",",
                    "    \"useDefineForClassFields\": true,",
                    "    \"lib\": [\"ES2020\", \"DOM\", \"DOM.Iterable\"],",
                    "    \"module\": \"ESNext\",",
                    "    \"skipLibCheck\": true,",
                    "    \"moduleResolution\": \"Bundler\",",
                    "    \"resolveJsonModule\": true,",
                    "    \"isolatedModules\": true,",
                    "    \"noEmit\": true,",
                    "    \"jsx\": \"react-jsx\",",
                    "    \"strict\": false",
                    "  },",
                    "  \"include\": [\"src\"],",
                    "  \"references\": [{ \"path\": \"./tsconfig.node.json\" }]",
                    "}",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "tsconfig.node.json"),
            "\n".join(
                [
                    "{",
                    "  \"compilerOptions\": {",
                    "    \"composite\": true,",
                    "    \"skipLibCheck\": true,",
                    "    \"module\": \"ESNext\",",
                    "    \"moduleResolution\": \"Bundler\"",
                    "  },",
                    "  \"include\": [\"vite.config.ts\"]",
                    "}",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "vite-env.d.ts"),
            "/// <reference types=\"vite/client\" />\n",
        )

        self._write_file(
            os.path.join(web_dir, "src", "actions.ts"),
            "\n".join(
                [
                    "export type ActionPayload = {",
                    "  action: string;",
                    "  args?: unknown[];",
                    "  kwargs?: Record<string, unknown>;",
                    "};",
                    "",
                    "export type ActionError = {",
                    "  message: string;",
                    "  type: string;",
                    "};",
                    "",
                    "export type ActionResponse<T> =",
                    "  | { ok: true; data: T }",
                    "  | { ok: false; error: ActionError };",
                    "",
                    "export type ActionClientOptions = {",
                    "  endpoint?: string;",
                    "  baseUrl?: string;",
                    "  fetcher?: typeof fetch;",
                    "};",
                    "",
                    "export function createActionClient(options: ActionClientOptions = {}) {",
                    "  const endpoint = options.endpoint ?? '/_actions';",
                    "  const baseUrl = options.baseUrl ?? '';",
                    "  const fetcher = options.fetcher ?? fetch;",
                    "  return async function callAction<T>(",
                    "    action: string,",
                    "    args: unknown[] = [],",
                    "    kwargs: Record<string, unknown> = {},",
                    "    init?: RequestInit,",
                    "  ): Promise<ActionResponse<T>> {",
                    "    const payload: ActionPayload = { action, args, kwargs };",
                    "    const response = await fetcher(baseUrl + endpoint, {",
                    "      method: 'POST',",
                    "      headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },",
                    "      body: JSON.stringify(payload),",
                    "      ...init,",
                    "    });",
                    "    return (await response.json()) as ActionResponse<T>;",
                    "  };",
                    "}",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "actions.client.ts"),
            "\n".join(
                [
                    "import { createActionClient, ActionClientOptions } from './actions';",
                    "",
                    "export function createActions(options: ActionClientOptions = {}) {",
                    "  const call = createActionClient(options);",
                    "  return {",
                    "    AppActions: {",
                    "      hello: (params: { name?: string } = {}) =>",
                    "        call<string>('AppActions.hello', [], params),",
                    "    },",
                    "    call,",
                    "  };",
                    "}",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "api", "client.ts"),
            "\n".join(
                [
                    "// Generated placeholder. Run:",
                    "// nestipy run web:build --spec http://127.0.0.1:8000/_router/spec --lang ts --output web/src/api/client.ts",
                    "",
                    "export type FetchLike = (input: RequestInfo, init?: RequestInit) => Promise<Response>;",
                    "",
                    "export interface ClientOptions {",
                    "  baseUrl: string;",
                    "  fetcher?: FetchLike;",
                    "  headers?: Record<string, string>;",
                    "}",
                    "",
                    "export class ApiClient {",
                    "  private _baseUrl: string;",
                    "  private _fetcher: FetchLike;",
                    "  private _headers: Record<string, string>;",
                    "",
                    "  constructor(options: ClientOptions) {",
                    "    this._baseUrl = options.baseUrl.replace(/\\/+$/, \"\");",
                    "    this._fetcher = options.fetcher ?? fetch;",
                    "    this._headers = options.headers ?? {};",
                    "  }",
                    "",
                    "  private _joinUrl(path: string): string {",
                    "    if (path.startsWith(\"http://\") || path.startsWith(\"https://\")) {",
                    "      return path;",
                    "    }",
                    "    return `${this._baseUrl}/${path.replace(/^\\/+/, \"\")}`;",
                    "  }",
                    "",
                    "  async ping(): Promise<string> {",
                    "    const url = this._joinUrl('/api/ping');",
                    "    const response = await this._fetcher(url, {",
                    "      method: 'GET',",
                    "      headers: { ...this._headers },",
                    "    });",
                    "    if (!response.ok) {",
                    "      throw new Error(await response.text());",
                    "    }",
                    "    return response.text();",
                    "  }",
                    "}",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "index.css"),
            "\n".join(
                [
                    "@tailwind base;",
                    "@tailwind components;",
                    "@tailwind utilities;",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "routes.tsx"),
            "\n".join(
                [
                    "import { createBrowserRouter } from 'react-router-dom';",
                    "",
                    "export const router = createBrowserRouter([",
                    "  { path: '/', element: <div /> },",
                    "]);",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "src", "main.tsx"),
            "\n".join(
                [
                    "import React from 'react';",
                    "import ReactDOM from 'react-dom/client';",
                    "import { RouterProvider } from 'react-router-dom';",
                    "import { router } from './routes';",
                    "import './index.css';",
                    "",
                    "ReactDOM.createRoot(document.getElementById('root')!).render(",
                    "  <React.StrictMode>",
                    "    <RouterProvider router={router} />",
                    "  </React.StrictMode>",
                    ");",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "tailwind.config.cjs"),
            "\n".join(
                [
                    "module.exports = {",
                    "  content: ['./index.html', './src/**/*.{ts,tsx}'],",
                    "  theme: {",
                    "    extend: {},",
                    "  },",
                    "  plugins: [],",
                    "};",
                    "",
                ]
            ),
        )

        self._write_file(
            os.path.join(web_dir, "postcss.config.cjs"),
            "\n".join(
                [
                    "module.exports = {",
                    "  plugins: {",
                    "    tailwindcss: {},",
                    "    autoprefixer: {},",
                    "  },",
                    "};",
                    "",
                ]
            ),
        )

        self._append_readme(
            destination,
            "\n".join(
                [
                    "",
                    "## Frontend (Nestipy Web)",
                    "",
                    "This project includes a Python-based frontend in `app/` plus a Vite scaffold in `web/`.",
                    "",
                    "Build + run both backend and frontend:",
                    "",
                    "```bash",
                    "nestipy start --dev --web --web-args \"--vite --install\"",
                    "```",
                    "",
                    "Regenerate typed action client (optional):",
                    "",
                    "```bash",
                    "nestipy run web:actions --spec http://127.0.0.1:8000/_actions/schema --output web/src/actions.client.ts",
                    "```",
                    "",
                    "Enable RouterSpec for typed HTTP client:",
                    "",
                    "```bash",
                    "export NESTIPY_ROUTER_SPEC=1",
                    "```",
                    "",
                    "Then generate the typed client:",
                    "",
                    "```bash",
                    "nestipy run web:build --spec http://127.0.0.1:8000/_router/spec --lang ts --output web/src/api/client.ts",
                    "```",
                    "",
                ]
            ),
        )

    @classmethod
    def mkdir(cls, name):
        path = os.path.join(os.getcwd(), "src", name)
        if not os.path.exists(path):
            os.mkdir(path)
            open(os.path.join(path, "__init__.py"), "a").close()
        return path

    def generate_resource_api(self, name):
        self.generate_dto(name)
        self.generate_service(name)
        self.generate_controller(name)
        self.generate_module(name)

    def generate_resource_graphql(self, name):
        self.generate_input(name)
        self.generate_service(name, prefix="graphql")
        self.generate_resolver(name)
        self.generate_module(name, prefix="graphql")

    def generate_command(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "command", prefix=prefix)

    def generate_module(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "module", prefix=prefix)
        self.modify_app_module(name)

    def generate_controller(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "controller", prefix=prefix)

    def generate_service(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "service", prefix=prefix)

    def generate_resolver(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "resolver", prefix=prefix)

    def generate_dto(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "dto", prefix=prefix)

    def generate_input(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, "input", prefix=prefix)

    def generate(self, name, parent_path, template, prefix: str = None):
        pref = f"{f'{prefix}_' if prefix is not None else ''}"
        content = self.generator.render_template(f"{pref}{template}.txt", name=name)
        file_path = str(os.path.join(parent_path, f"{name.lower()}_{template}.py"))
        f = open(file_path, "w+")
        f.write(content)
        f.close()

    @classmethod
    def modify_app_module(cls, name):
        module_name = str(name).capitalize() + "Module"
        app_path = os.path.join(os.getcwd(), "app_module.py")
        new_import_statement = (
            f"from src.{name.lower()}.{name.lower()}_module import {module_name}"
        )

        if os.path.exists(app_path):
            with open(app_path, "r") as file:
                file_content = file.read()
            # Check if the import statement already exists; if not, add it
            if new_import_statement not in file_content:
                file_content = new_import_statement + "\n" + file_content

            # Match the @Module decorator
            module_pattern = r"@Module\s*\(\s*(.*?)\s*\)\s*class"
            match = re.search(module_pattern, file_content, re.DOTALL)

            if match:
                # Extract the current content inside the @Module decorator
                module_body = match.group(1)
                # Search for the 'imports' property in the @Module body
                imports_match = re.search(
                    r"imports\s*=\s*\[\s*((?:[^\[\]]+|\[[^\[\]]*\])*)\s*\]",
                    module_body,
                    re.DOTALL,
                )

                if imports_match:
                    # 'imports' exists; extract its content
                    imports_content = imports_match.group(1).strip()

                    # If the module is not already in the imports, add it
                    if module_name not in imports_content:
                        if imports_content and not imports_content.endswith(","):
                            imports_content += (
                                ","  # Ensure comma before adding new import
                            )

                        new_imports = f"{imports_content}\n\t{module_name}"
                        updated_module_body = re.sub(
                            r"imports\s*=\s*\[\s*((?:[^\[\]]+|\[[^\[\]]*\])*)\s*\]",
                            f"imports=[\n\t{new_imports}\n]",
                            module_body,
                            flags=re.DOTALL,
                        )
                    else:
                        updated_module_body = module_body
                else:
                    # If 'imports' doesn't exist, add it to the @Module properties
                    updated_module_body = (
                        module_body.strip() + f",\n\timports=[\n\t{module_name}\n]"
                    )

                # Replace the old @Module body with the updated one
                updated_content = file_content.replace(module_body, updated_module_body)

                # Clean, sort, and format the final code
                cleaned_code = autoflake.fix_code(updated_content)
                sorted_code = isort.code(cleaned_code)
                formatted_code = autopep8.fix_code(sorted_code)

                # Write the updated content back to the file
                with open(app_path, "w") as file:
                    file.write(formatted_code)
            else:
                print("No @Module decorator found in app_module.py.")
