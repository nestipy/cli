import asyncio
import atexit
import importlib
import os
import sys
import warnings
from pathlib import Path
from subprocess import DEVNULL, check_call
from typing import Literal

import questionary
import rich_click as click
import shutil
import subprocess
from click_aliases import ClickAliasedGroup
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from yaspin import yaspin

from . import frontend
from .handler import NestipyCliHandler
from .repl import REPL
from .server import (
    GranianStartConfig,
    build_logging_config,
    configure_logging,
    create_granian_instance,
    ensure_log_dir,
    granian_log_prefixer,
    select_port,
    write_logging_config,
)
from .style import CliStyle

console = Console()

handler = NestipyCliHandler()
echo = CliStyle()


@click.group(cls=ClickAliasedGroup)
def main():
    click.clear()


@main.command(aliases=["n"])
@click.argument("name")
@click.option(
    "--full",
    is_flag=True,
    default=False,
    help="Fullstack scaffold: database + auth + Inertia frontend.",
)
@click.option(
    "--fullstack",
    is_flag=True,
    default=False,
    help="Lean Inertia.js scaffold (backend + Inertia frontend).",
)
@click.option("--react", is_flag=True, default=False, help="Use React for the Inertia frontend.")
@click.option("--vue", is_flag=True, default=False, help="Use Vue for the Inertia frontend.")
@click.option("--svelte", is_flag=True, default=False, help="Use Svelte for the Inertia frontend.")
def new(name, full: bool, fullstack: bool, react: bool, vue: bool, svelte: bool):
    """Create new project"""
    click.clear()

    chosen = [fw for fw, on in (("react", react), ("vue", vue), ("svelte", svelte)) if on]
    if len(chosen) > 1:
        echo.error("Choose only one frontend framework (--react, --vue or --svelte).")
        return
    framework = chosen[0] if chosen else None

    wants_frontend = full or fullstack
    if wants_frontend and framework is None:
        framework = (
            questionary.select(
                "Choose a frontend framework for Inertia:",
                choices=list(frontend.FRAMEWORKS),
                default="react",
            ).ask()
            or "react"
        )

    destination = handler.create_project(name, full=full, fullstack=fullstack)
    if destination is None:
        echo.error(f"Folder {name} already exist.")
        return

    run_hint = (
        "\n\tnestipy start --dev --web   # runs backend + Inertia frontend together"
        if wants_frontend
        else "\n\tnestipy start --dev"
    )
    message = (
        f"Project {name} created successfully.\nStart your project by running:\n\tcd {name}"
        f"\n\tuv sync{run_hint}"
    )
    echo.info(message)

    if wants_frontend:
        if not frontend.npm_available():
            echo.warning(
                "npm not found — skipped frontend generation. Install Node 18+, then run:"
                f"\n\tnpm create vite@latest inertia -- --template {framework}-ts"
            )
            return
        echo.info(f"Generating {framework} Inertia frontend (npm create vite)...")
        try:
            frontend.scaffold_inertia_frontend(destination, framework)
            echo.success(
                "Frontend generated in inertia/.\n"
                "`nestipy start --dev --web` runs the backend and this frontend together, "
                "or run it alone with:\n\tcd inertia\n\tnpm run dev"
            )
        except Exception as exc:  # noqa: BLE001
            echo.error(f"Frontend generation failed: {exc}")
            echo.info(
                "Retry manually:"
                f"\n\tnpm create vite@latest inertia -- --template {framework}-ts"
            )


@main.command(name="doctor")
def doctor() -> None:
    """Check environment requirements for Nestipy."""
    errors = 0

    echo.info("Nestipy doctor check")

    py_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if sys.version_info < (3, 11):
        echo.error(f"[DOCTOR] Python {py_version} (requires >= 3.11)")
        errors += 1
    else:
        echo.success(f"[DOCTOR] Python {py_version} OK")

    try:
        import nestipy  # type: ignore

        version = getattr(nestipy, "__version__", "unknown")
        echo.success(f"[DOCTOR] nestipy {version} OK")
    except Exception as exc:
        echo.error(f"[DOCTOR] nestipy import failed: {exc}")
        errors += 1

    try:
        import granian  # type: ignore

        version = getattr(granian, "__version__", "unknown")
        echo.success(f"[DOCTOR] granian {version} OK")
    except Exception as exc:
        echo.warning(f"[DOCTOR] granian import failed: {exc}")

    node_path = shutil.which("node")
    if not node_path:
        echo.warning(
            "[DOCTOR] Node.js not found (needed only for an Inertia frontend; install Node 18+)."
        )
    else:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        node_version = (result.stdout or result.stderr or "").strip() or "unknown"
        echo.success(f"[DOCTOR] Node {node_version} OK")

    if errors:
        sys.exit(1)


@main.group(cls=ClickAliasedGroup, name="generate", aliases=["g", "gen"])
def make():
    """Generate resource, module, controller, service, resolver, graphql input"""
    pass


@main.command(name="start")
@click.argument("app_path", default="main:app")
@click.option("-D", "--dev", is_flag=True, default=False, help="Development server")
@click.option("-P", "--port", required=False, default=8000, help="Server port")
@click.option("-H", "--host", required=False, default="0.0.0.0", help="Server host")
@click.option("--workers", default=1, type=int, help="Number of worker processes.")
@click.option("--ssl-keyfile", type=str, help="SSL certificate key.")
@click.option("--ssl-cert-file", type=str, help="SSL certificate file.")
@click.option("--loop", type=str, help="Event loop.", default="auto")
@click.option("--http", type=str, help="HTTP protocol version.", default="auto")
@click.option(
    "--reload-any",
    is_flag=True,
    default=False,
    help="Reload on any file change (disable python-only filter).",
)
@click.option(
    "--reload-path",
    "reload_paths",
    multiple=True,
    help="Additional paths to watch for reload (can be set multiple times).",
)
@click.option(
    "--reload-ignore-dir",
    "reload_ignore_dirs",
    multiple=True,
    help="Directory names to ignore for reload (can be set multiple times).",
)
@click.option(
    "--reload-ignore-pattern",
    "reload_ignore_patterns",
    multiple=True,
    help="Regex patterns to ignore for reload (can be set multiple times).",
)
@click.option(
    "--reload-ignore-path",
    "reload_ignore_paths",
    multiple=True,
    help="Absolute paths to ignore for reload (can be set multiple times).",
)
@click.option(
    "--reload-tick",
    type=int,
    default=None,
    help="Polling interval in ms for reload (if supported by Granian).",
)
@click.option(
    "--reload-ignore-worker-failure",
    is_flag=True,
    default=False,
    help="Ignore worker failure during reload (if supported by Granian).",
)
@click.option(
    "--web",
    is_flag=True,
    default=False,
    help="In dev, also run the Inertia frontend dev server (npm run dev in ./inertia).",
)
@click.option(
    "--web-dir",
    default="inertia",
    help="Frontend directory for --web (default: inertia).",
)
def start(
    app_path: str,
    dev: bool,
    port: int,
    host: str,
    workers: int,
    ssl_keyfile: str,
    ssl_cert_file,
    loop: Literal["auto", "asyncio", "rloop", "uvloop"],
    http: Literal["auto", "1", "2"],
    reload_any: bool,
    reload_paths: tuple[str, ...],
    reload_ignore_dirs: tuple[str, ...],
    reload_ignore_patterns: tuple[str, ...],
    reload_ignore_paths: tuple[str, ...],
    reload_tick: int | None,
    reload_ignore_worker_failure: bool,
    web: bool,
    web_dir: str,
) -> None:
    """Starting nestipy server"""
    try:
        import nestipy  # noqa: F401
    except ImportError:
        with yaspin(text="Installing nestipy ...", color="blue") as spinner:
            spinner.color = "blue"
            check_call(
                [sys.executable, "-m", "pip", "install", "pip", "--upgrade"],
                stdout=DEVNULL,
            )
            check_call(
                [sys.executable, "-m", "pip", "install", "nestipy", "--upgrade"],
                stdout=DEVNULL,
            )
            spinner.color = "green"
            spinner.ok("✔")
        importlib.import_module("nestipy")
    try:
        import granian  # noqa: F401
    except ImportError:
        with yaspin(text="Installing granian ...", color="blue") as spinner:
            spinner.color = "blue"
            check_call(
                [sys.executable, "-m", "pip", "install", "pip", "--upgrade"],
                stdout=DEVNULL,
            )
            check_call(
                [sys.executable, "-m", "pip", "install", "granian[reload]", "--upgrade"],
                stdout=DEVNULL,
            )
            spinner.color = "green"
            spinner.ok("✔")

    module_path, app_name = app_path.split(":")
    module_file_path = Path(module_path).resolve()
    module_name = module_file_path.stem
    sys.path.append(str(module_file_path.parent))

    def import_app():
        mod = importlib.import_module(module_name)
        app_ = getattr(mod, app_name)
        return mod, app_

    m, app = import_app()
    from nestipy.core import NestipyApplication, NestipyMicroservice

    is_ms: bool = isinstance(app, NestipyMicroservice) and not isinstance(
        app, NestipyApplication
    )
    config = build_logging_config(dev)
    configure_logging(config)
    if not dev:
        ensure_log_dir()
    environment = "Development" if dev else "Production"
    selected_port = select_port(port, is_ms)
    scheme = "https" if ssl_cert_file else "http"
    multiline_text = Text(style=Style(color="green"))
    if is_ms:
        multiline_text.append(
            "Microservice server running ...", Style(bold=True, color="green")
        )
    else:
        multiline_text.append(f"Serving at: {scheme}://{host}:{selected_port}")
        if dev:
            multiline_text.append(
                f"\nDev server running on: {scheme}://{host}:{selected_port}",
                Style(bold=True, color="green"),
            )
    multiline_text.append(f"\nRunning in {environment.lower()} mode")
    if dev:
        multiline_text.append("\nFor production, use : ")
        multiline_text.append("nestipy start", Style(bold=True, color="green"))

    panel = Panel(
        multiline_text,
        title=f"Nestipy CLI - {environment} mode",
        box=ROUNDED,
        border_style=Style(bold=True, encircle=True, color="green", dim=True),
        width=50,
        padding=(0, 1, 0, 6),
        highlight=True,
        style=Style(color="green"),
    )
    console.print(panel)
    if is_ms and not dev:
        asyncio.run(app.start())

    log_config_path = write_logging_config(config)
    project_root = module_file_path.parent.resolve()
    cwd_root = Path.cwd().resolve()

    def _abs_path(value: str) -> str:
        if os.path.isabs(value):
            return value
        return str((project_root / value).resolve())

    reload_ignore_paths_list = [_abs_path(p) for p in reload_ignore_paths]
    reload_ignore_dirs_list = list(reload_ignore_dirs)
    if (project_root / "app").exists() and "app" not in reload_ignore_dirs_list:
        reload_ignore_dirs_list.append("app")
    if (project_root / "page").exists() and "page" not in reload_ignore_dirs_list:
        reload_ignore_dirs_list.append("page")
    if (project_root / "inertia").exists() and "inertia" not in reload_ignore_dirs_list:
        reload_ignore_dirs_list.append("inertia")
    if web_dir and web_dir not in reload_ignore_dirs_list:
        reload_ignore_dirs_list.append(web_dir)
    if cwd_root != project_root:
        if (cwd_root / "app").exists() and "app" not in reload_ignore_dirs_list:
            reload_ignore_dirs_list.append("app")
        if (cwd_root / "page").exists() and "page" not in reload_ignore_dirs_list:
            reload_ignore_dirs_list.append("page")
    reload_paths_list = [_abs_path(p) for p in reload_paths]
    if dev and not reload_any and not reload_paths_list:
        reload_paths_list.append(str(project_root))

    # --web (dev only): run the Inertia frontend dev server (vite) alongside the backend
    web_process = None
    if web and dev:
        web_path = project_root / web_dir
        if not web_path.exists():
            echo.warning(
                f"[WEB] '{web_dir}/' not found — skipping frontend dev server."
            )
        elif not shutil.which("npm"):
            echo.warning("[WEB] npm not found — skipping frontend dev server.")
        else:
            if not (web_path / "node_modules").exists():
                echo.info("[WEB] Installing frontend dependencies (npm install)...")
                subprocess.run(["npm", "install"], cwd=str(web_path), check=False)
            echo.info(f"[WEB] Starting Inertia dev server (npm run dev in {web_dir}/)...")
            web_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=str(web_path),
                env=os.environ.copy(),
            )

            def _terminate_web() -> None:
                if web_process and web_process.poll() is None:
                    web_process.terminate()

            atexit.register(_terminate_web)
    elif web and not dev:
        echo.warning(
            "[WEB] --web only runs the frontend dev server in --dev. "
            "In production, build it (npm run build) and serve the dist via Inertia."
        )

    server = create_granian_instance(
        GranianStartConfig(
            app_path=app_path,
            dev=dev,
            host=host,
            port=selected_port,
            workers=workers,
            ssl_keyfile=ssl_keyfile,
            ssl_cert_file=ssl_cert_file,
            loop=loop,
            http=http,
            is_microservice=is_ms,
            log_config_path=log_config_path,
            reload_any=reload_any,
            reload_paths=reload_paths_list,
            reload_ignore_dirs=reload_ignore_dirs_list,
            reload_ignore_patterns=list(reload_ignore_patterns),
            reload_ignore_paths=reload_ignore_paths_list,
            reload_tick=reload_tick,
            reload_ignore_worker_failure=reload_ignore_worker_failure,
        )
    )
    with granian_log_prefixer():
        server.serve()


@make.command(name="resource", aliases=["r", "res"])
@click.argument("name")
def resource(name: str) -> None:
    """Create new resource for project."""
    name = str(name).lower()
    choice = questionary.select(
        "Select resource type:", choices=["api", "graphql"]
    ).ask()
    if choice == "graphql":
        handler.generate_resource_graphql(name)
    else:
        handler.generate_resource_api(name)
    echo.success(f"Resource created successfully inside src/{name}.")


@make.command(aliases=["mod"])
@click.argument("name")
def module(name):
    """Create new module"""
    name = str(name).lower()
    handler.generate_module(name, prefix="single")
    echo.success(f"Module created successfully inside src/{name}.")


@make.command(aliases=["ctrl"])
@click.argument("name")
def controller(name):
    """Create new controller"""
    name = str(name).lower()
    handler.generate_controller(name, prefix="single")
    echo.success(f"Controller created successfully inside src/{name}.")


@make.command(aliases=["cmd"])
@click.argument("name")
def command(name):
    """Create new command"""
    name = str(name).lower()
    handler.generate_command(name)
    echo.success(f"Command created successfully inside src/{name}.")


@make.command()
@click.argument("name")
def resolver(name):
    """Create new graphql resolver"""
    handler.generate_resolver(name, prefix="single")
    echo.success(f"Resolver created successfully inside src/{name}.")


@make.command()
@click.argument("name")
def service(name):
    """Create new service"""
    name = str(name).lower()
    handler.generate_service(name, prefix="single")
    echo.success(f"Service created successfully inside src/{name}.")


@make.command(name="input")
@click.argument("name")
def graphql_input(name):
    """Create new graphql input"""
    name = str(name).lower()
    handler.generate_service(name, prefix="single")
    echo.success(f"Graphql Input created successfully inside src/{name}.")


@main.command(
    context_settings={"ignore_unknown_options": True},
)
@click.option("-P", "--path", default="cli:command", help="Command path")
@click.argument("name", required=True)
@click.argument("args", nargs=-1, required=False, type=click.UNPROCESSED)
def run(path: str, name: str, args: any):
    """Run nestipy commander app"""
    module_path, cmd_name = path.split(":")
    module_file_path = Path(module_path).resolve()
    module_name = module_file_path.stem
    sys.path.append(str(module_file_path.parent))
    mod = importlib.import_module(module_name)
    cmd = getattr(mod, cmd_name)
    asyncio.run(cmd.run(name, args))


@main.command(name="repl")
@click.option("-P", "--path", default="main:app", help="Nestipy Application path")
def repl(path: str):
    """Run nestipy REPL"""
    module_path, app_name = path.split(":")
    module_file_path = Path(module_path).resolve()
    module_name = module_file_path.stem
    sys.path.append(str(module_file_path.parent))
    mod = importlib.import_module(module_name)
    app = getattr(mod, app_name)
    repl_ = REPL(app)
    warnings.simplefilter("ignore", category=RuntimeWarning)
    repl_.interact(banner="Nestipy REPL", exitmsg="Exiting REPL ...")


if __name__ == "__main__":
    main()
