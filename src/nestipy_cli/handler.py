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
                    "from nestipy.web import component, h, Slot",
                    "",
                    "@component",
                    "def Layout():",
                    "    return h.div(",
                    "        h.header(\"Nestipy Web\", class_name=\"text-xl font-semibold\"),",
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
                    "    create_context,",
                    ")",
                    "",
                    "AppContext = create_context(\"Nestipy\")",
                    "",
                    "@component",
                    "def Page():",
                    "    message, set_message = use_state(\"Loading...\")",
                    "    ctx = use_context(AppContext)",
                    "    reload = use_callback(",
                    "        js(\"\"\"() => {",
                    "  fetch('/_actions', {",
                    "    method: 'POST',",
                    "    headers: { 'Content-Type': 'application/json' },",
                    "    body: JSON.stringify({ action: 'AppActions.hello', kwargs: { name: ctx } })",
                    "  })",
                    "    .then(r => r.json())",
                    "    .then(r => {",
                    "      if (r.ok) { set_message(r.data); }",
                    "      else { set_message(r.error?.message ?? 'Error'); }",
                    "    });",
                    "}\"\"\"),",
                    "        deps=[ctx],",
                    "    )",
                    "    upper = use_memo(js(\"() => (message ?? '').toUpperCase()\"), deps=[message])",
                    "    use_effect(js(\"() => { reload(); }\"), deps=[reload])",
                    "    return h.div(",
                    "        h.h1(\"Nestipy Web + Actions\"),",
                    "        h.p(js(\"message\"), class_name=\"text-sm text-slate-200\"),",
                    "        h.p(js(\"upper\"), class_name=\"text-xs text-slate-400\"),",
                    "        h.button(",
                    "            \"Reload\",",
                    "            on_click=js(\"reload\"),",
                    "            class_name=\"px-3 py-1 rounded bg-blue-600 text-white\",",
                    "        ),",
                    "        class_name=\"space-y-3\",",
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
