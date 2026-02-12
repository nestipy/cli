import asyncio
import importlib
import sys
import warnings
import atexit
import os
import shlex
import subprocess
from pathlib import Path
from subprocess import DEVNULL, check_call
from typing import Literal

import questionary
import rich_click as click
from click_aliases import ClickAliasedGroup
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from yaspin import yaspin

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
    "--frontend",
    is_flag=True,
    default=False,
    help="Include Nestipy Web scaffold with hooks + actions example.",
)
def new(name, frontend: bool):
    """Create new project"""
    # if not shutil.which('poetry'):
    # curl -sSL https://install.python-poetry.org | python3 -
    click.clear()
    created = handler.create_project(name, frontend=frontend)
    if not created:
        echo.error(f"Folder {name} already exist.")
        return
    message = (
        f"Project {name} created successfully.\nStart your project by running:\n\tcd {name}"
        f"\n\tuv sync \n\tnestipy start --dev"
    )
    if frontend:
        message += (
            "\n\nFrontend dev (Vite + backend):"
            "\n\tnestipy start --dev --web --web-args \"--vite --install\""
        )
    echo.info(message)
    # else:
    #     echo.error(f"Nestipy need poetry as dependency manager.")


@main.group(cls=ClickAliasedGroup, name="generate", aliases=["g", "gen"])
def make():
    """Generate resource, module, controller, service, resolver, graphql input"""
    pass


current_task = None


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
    help="Start Nestipy Web dev server alongside the backend.",
)
@click.option(
    "--web-args",
    default="",
    help="Extra arguments passed to `nestipy run web:dev`.",
)
@click.option(
    "--web-proxy",
    default=None,
    help="Proxy URL for web dev server (defaults to backend address).",
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
    web_args: str,
    web_proxy: str | None,
) -> None:
    """Starting nestipy server"""
    try:
        import nestipy
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
    from nestipy.core import NestipyMicroservice, NestipyApplication

    is_ms: bool = isinstance(app, NestipyMicroservice) and not isinstance(
        app, NestipyApplication
    )
    config = build_logging_config(dev)
    configure_logging(config)
    if not dev:
        ensure_log_dir()
    environment = "Development" if dev else "Production"
    scheme = "https" if ssl_cert_file else "http"
    multiline_text = Text(style=Style(color="green"))
    if is_ms:
        multiline_text.append(
            "Microservice server running ...", Style(bold=True, color="green")
        )
    else:
        multiline_text.append(f"Serving at: {scheme}://{host}:{port}")
    multiline_text.append(f"\nRunning in {environment.lower()} mode")
    if dev:
        multiline_text.append("\nFor production, use : ")
        multiline_text.append("nestipy start", Style(bold=True, color="green"))

    panel = Panel(
        multiline_text,
        title=f"Nestipy CLI - {environment} mode",
        box=ROUNDED,
        border_style=Style(
            bold=True,
            encircle=True,
            color="green",
            dim=True,
        ),
        width=50,
        padding=(0, 1, 0, 6),
        highlight=True,
        style=Style(color="green"),
    )
    console.print(panel)
    if is_ms and not dev:
        asyncio.run(app.start())

    log_config_path = write_logging_config(config)
    selected_port = select_port(port, is_ms)
    web_process = None
    if web:
        def _has_flag(args: list[str], flag: str) -> bool:
            return any(arg == flag or arg.startswith(flag + "=") for arg in args)

        def _strip_backend_flags(args: list[str]) -> list[str]:
            cleaned: list[str] = []
            skip_next = False
            for arg in args:
                if skip_next:
                    skip_next = False
                    continue
                if arg in {"--backend", "--backend-cwd"}:
                    skip_next = True
                    continue
                if arg.startswith("--backend=") or arg.startswith("--backend-cwd="):
                    continue
                cleaned.append(arg)
            return cleaned

        web_args_list = shlex.split(web_args) if web_args else ["--vite"]
        web_args_list = _strip_backend_flags(web_args_list)
        if not _has_flag(web_args_list, "--proxy") and not os.getenv("NESTIPY_WEB_PROXY"):
            proxy_value = web_proxy or f"{scheme}://{host}:{selected_port}"
            web_args_list.extend(["--proxy", proxy_value])
        env = os.environ.copy()
        env["NESTIPY_WEB_BACKEND"] = ""
        env["NESTIPY_WEB_BACKEND_CWD"] = ""
        web_process = subprocess.Popen(
            ["nestipy", "run", "web:dev", *web_args_list],
            cwd=str(module_file_path.parent),
            env=env,
        )
        atexit.register(lambda: web_process and web_process.terminate())
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
            reload_paths=list(reload_paths),
            reload_ignore_dirs=list(reload_ignore_dirs),
            reload_ignore_patterns=list(reload_ignore_patterns),
            reload_ignore_paths=list(reload_ignore_paths),
            reload_tick=reload_tick,
            reload_ignore_worker_failure=reload_ignore_worker_failure,
        )
    )
    with granian_log_prefixer():
        server.serve()


@make.command(name="resource", aliases=["r", "res"])
@click.argument("name")
def resource(name: str) -> None:
    """Create new resource for project.
    :rtype: object
    :param name:
    :type name:
    """
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
    """Create new controller"""
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
    """Create new service"""
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
