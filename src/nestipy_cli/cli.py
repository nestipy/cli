import asyncio
import importlib
import sys
import warnings
import atexit
import os
import shlex
import subprocess
import threading
import re
import time
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
    "--web",
    is_flag=True,
    default=False,
    help="Include Nestipy Web scaffold with hooks + actions example.",
)
@click.option(
    "--ssr/--no-ssr",
    default=False,
    help="Include optional SSR scaffold (requires --web).",
)
def new(name, web: bool, ssr: bool):
    """Create new project"""
    # if not shutil.which('poetry'):
    # curl -sSL https://install.python-poetry.org | python3 -
    click.clear()
    if ssr and not web:
        web = True
    created = handler.create_project(name, web=web, web_ssr=ssr)
    if not created:
        echo.error(f"Folder {name} already exist.")
        return
    message = (
        f"Project {name} created successfully.\nStart your project by running:\n\tcd {name}"
        f"\n\tuv sync \n\tnestipy start --dev"
    )
    if web:
        show_web_install_log = os.getenv("NESTIPY_WEB_INSTALL_LOG", "0") in {"1", "true", "yes", "on"}
        message += (
            "\n\nFrontend dev (Vite + backend):"
            "\n\tnestipy start --dev --web --web-args \"--vite --install\""
        )
        if ssr:
            message += (
                "\n\nSSR build + run:"
                "\n\tpip install \"nestipy[web-ssr]\""
                "\n\tnestipy run web:build --vite --ssr"
                "\n\tnestipy start --web --ssr --ssr-runtime jsrun"
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
@click.option(
    "--ssr/--no-ssr",
    default=False,
    help="Enable optional SSR when serving web dist.",
)
@click.option(
    "--ssr-runtime",
    default=None,
    help="SSR runtime (jsrun or node).",
)
@click.option(
    "--ssr-entry",
    default=None,
    help="Path to SSR entry bundle (default: web/dist/ssr/entry-server.js).",
)
@click.option(
    "--action-security/--no-action-security",
    default=None,
    help="Enable or disable default action security presets.",
)
@click.option(
    "--action-origins",
    default=None,
    help="Comma-separated list of allowed action origins.",
)
@click.option(
    "--action-allow-missing-origin/--no-action-allow-missing-origin",
    default=None,
    help="Allow missing Origin header for actions.",
)
@click.option(
    "--action-csrf/--no-action-csrf",
    default=None,
    help="Enable or disable CSRF guard for actions.",
)
@click.option(
    "--action-signature-secret",
    default=None,
    help="Secret for action HMAC signatures.",
)
@click.option(
    "--action-permissions/--no-action-permissions",
    default=None,
    help="Enable or disable ActionPermissionGuard in presets.",
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
    ssr: bool,
    ssr_runtime: str | None,
    ssr_entry: str | None,
    action_security: bool | None,
    action_origins: str | None,
    action_allow_missing_origin: bool | None,
    action_csrf: bool | None,
    action_signature_secret: str | None,
    action_permissions: bool | None,
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

    if action_security is not None:
        os.environ["NESTIPY_ACTION_SECURITY"] = "1" if action_security else "0"
    if action_origins:
        os.environ["NESTIPY_ACTION_ALLOWED_ORIGINS"] = action_origins
    if action_allow_missing_origin is not None:
        os.environ["NESTIPY_ACTION_ALLOW_MISSING_ORIGIN"] = (
            "1" if action_allow_missing_origin else "0"
        )
    if action_csrf is not None:
        os.environ["NESTIPY_ACTION_CSRF"] = "1" if action_csrf else "0"
    if action_signature_secret is not None:
        os.environ["NESTIPY_ACTION_SIGNATURE_SECRET"] = action_signature_secret
    if action_permissions is not None:
        os.environ["NESTIPY_ACTION_PERMISSIONS"] = "1" if action_permissions else "0"

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
    project_root = module_file_path.parent.resolve()
    cwd_root = Path.cwd().resolve()
    web_process = None
    web_app_dir = None
    if web:
        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        if dev:
            os.environ["NESTIPY_WEB_DEV"] = "1"
        if ssr:
            os.environ["NESTIPY_WEB_SSR"] = "1"
        if ssr_runtime:
            os.environ["NESTIPY_WEB_SSR_RUNTIME"] = ssr_runtime
        if ssr_entry:
            os.environ["NESTIPY_WEB_SSR_ENTRY"] = ssr_entry

        def _strip_ansi(text: str) -> str:
            return ansi_re.sub("", text)

        # Your existing functions
        def _stream_web_logs(stream) -> None:
            try:
                for raw in iter(stream.readline, ""):
                    _handle_web_log(raw)
            except ValueError:
                return
            finally:
                try:
                    stream.close()
                except Exception:
                    pass

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

        def _extract_web_app_dir(args: list[str]) -> str:
            for i, arg in enumerate(args):
                if arg == "--app-dir" and i + 1 < len(args):
                    return args[i + 1]
                if arg.startswith("--app-dir="):
                    return arg.split("=", 1)[1]
            return "app"

        def _extract_web_out_dir(args: list[str]) -> str:
            for i, arg in enumerate(args):
                if arg in {"--out-dir", "--out"} and i + 1 < len(args):
                    return args[i + 1]
                if arg.startswith("--out-dir=") or arg.startswith("--out="):
                    return arg.split("=", 1)[1]
            return "web"

        def _extract_flag_value(args: list[str], flag: str) -> str | None:
            for i, arg in enumerate(args):
                if arg == flag and i + 1 < len(args):
                    return args[i + 1]
                if arg.startswith(flag + "="):
                    return arg.split("=", 1)[1]
            return None

        # New helper functions
        def _handle_file_change(line: str) -> None:
            """Process file change events from Vite"""
            text = re.sub(r'\x1b\[[0-9;]*m', '', line).strip()
            match = re.search(r"\[vite\]\s+(.+)", text)
            if match:
                payload = match.group(1).strip()
                if payload.startswith("(client)"):
                    payload = payload.replace("(client)", "").strip()
                lower_payload = payload.lower()
                if lower_payload.startswith("hmr update"):
                    payload = payload[len("hmr update"):].strip()
                    message = f"[NESTIPY] INFO [WEB] File changed HMR UPDATE {payload}"
                elif lower_payload.startswith("page reload"):
                    payload = payload[len("page reload"):].strip()
                    message = f"[NESTIPY] INFO [WEB] File changed PAGE RELOAD {payload}"
                else:
                    message = f"[NESTIPY] INFO [WEB] File changed {payload}"
                echo.info(message)
                return

            parts = text.split()
            if len(parts) < 2:
                return

            change_type = parts[0]
            file_path = " ".join(parts[1:]).strip()

            if change_type == "✓":
                change_type = "updated"
            elif change_type == "✗":
                change_type = "error"

            message = f"[NESTIPY] INFO [WEB] File changed {change_type.upper()} {file_path}"
            echo.info(message)

        def _handle_build_progress(line: str) -> None:
            """Process build progress messages from Vite"""
            if "compiled successfully" in line.lower():
                match = re.search(r"(\d+\.\d+)ms", line)
                if match:
                    time_ms = match.group(1)
                    echo.success(f"[NESTIPY] BUILD SUCCESS [WEB] Compiled in {time_ms}")
                else:
                    echo.success(f"[NESTIPY] BUILD SUCCESS [WEB] Compiled successfully")
                return

            if "transforming" in line.lower() or "compiling" in line.lower():
                match = re.search(r"transforming|compiling\s+(.+)", line, re.IGNORECASE)
                if match:
                    file_path = match.group(1).strip()
                    echo.info(f"[NESTIPY] BUILD PROGRESS [WEB] Processing {file_path}")
                else:
                    echo.info(f"[NESTIPY] BUILD PROGRESS [WEB] {line}")
                return

            if "error" in line.lower():
                echo.error(f"[NESTIPY] BUILD ERROR [WEB] {line}")
                return

        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        web_log_level = os.getenv("NESTIPY_WEB_LOG_LEVEL", "normal").lower()
        show_web_install_log = os.getenv("NESTIPY_WEB_INSTALL_LOG", "0") in {
            "1",
            "true",
            "yes",
            "on",
        }
        web_dev_reported = False
        web_dev_fallback_url = None

        def _strip_ansi(text: str) -> str:
            return ansi_re.sub("", text)

        # Enhanced log handler
        def _handle_web_log(line: str) -> None:
            nonlocal web_dev_reported
            text = _strip_ansi(line).strip()
            if not text:
                return

            lower = text.lower()

            if web_log_level != "verbose":
                if lower.startswith("> ") or lower.startswith("vite v") or "press h + enter" in lower:
                    return
                if "local:" in lower or "network:" in lower:
                    match = re.search(r"(https?://\S+)", text)
                    if match and web_log_level != "silent":
                        url = match.group(1).rstrip(")")
                        if (
                            "localhost" in url
                            or "127.0.0.1" in url
                            or "0.0.0.0" in url
                        ):
                            echo.success(f"[NESTIPY] INFO [WEB] Dev server: {url}")
                            if not web_dev_reported:
                                # echo.info(
                                #     f"[NESTIPY] INFO [WEB] Dev server running on: {url}"
                                # )
                                web_dev_reported = True
                    return

            if lower.startswith("traceback") or "exception" in lower or "importerror" in lower:
                echo.error(f"[NESTIPY] ERROR [WEB] {text}")
                return
            if text.lstrip().startswith('File "') or text.lstrip().startswith("File "):
                echo.error(f"[NESTIPY] ERROR [WEB] {text}")
                return

            if text.startswith("[NESTIPY] INFO [WEB]"):
                payload = text[len("[NESTIPY] INFO [WEB]") :].strip()
                payload_lower = payload.lower()
                if web_log_level != "verbose":
                    if payload_lower.startswith("> ") or payload_lower.startswith("vite v"):
                        return
                    if "press h + enter" in payload_lower:
                        return
                    if "local:" in payload_lower or "network:" in payload_lower:
                        return
                echo.info(text)
                return

            if "install:" in lower and "[web]" in lower:
                echo.info(text)
                return

            if "audited" in lower or "packages are looking for funding" in lower or "found 0 vulnerabilities" in lower:
                return
            if show_web_install_log and (
                "added" in lower
                or "up to date" in lower
                or "installed" in lower
                or "packages:" in lower
            ):
                echo.info(f"[NESTIPY] INFO [WEB] {text}")
                return

            if web_log_level in {"quiet", "normal"} and text.startswith("VITE v") and "ready in" not in text:
                return

            match = re.search(r"(https?://\S+)", text)
            if match and web_log_level != "silent":
                url = match.group(1).rstrip(")")
                normalized = re.sub(r"^[^\w]+", "", text.strip())
                is_local_line = "local:" in normalized.lower()
                is_network_line = "network:" in normalized.lower()
                if (
                    "localhost" in url
                    or "127.0.0.1" in url
                    or "0.0.0.0" in url
                    or text.strip().startswith("Local:")
                    or text.strip().startswith("Network:")
                ):
                    echo.success(f"[NESTIPY] INFO [WEB] Dev server: {url}")
                    if not web_dev_reported and (is_local_line or is_network_line or "vite" in lower):
                        echo.success(f"[NESTIPY] INFO [WEB] Dev server running on: {url}")
                    web_dev_reported = True
                    return

            if text.startswith("(!)") or "failed to" in lower or "warning" in lower:
                echo.warning(f"[NESTIPY] WARNING [WEB] {text}")
                return
            if "error" in lower:
                echo.error(f"[NESTIPY] ERROR [WEB] {text}")
                return

            if web_log_level in {"normal", "verbose"}:
                if (
                    "updated" in lower
                    or "created" in lower
                    or "deleted" in lower
                    or "hmr" in lower
                    or "hot updated" in lower
                    or "page reload" in lower
                ):
                    _handle_file_change(text)
                    return

                if "transforming" in lower or "compiling" in lower or "building" in lower:
                    _handle_build_progress(text)
                    return

            if web_log_level == "verbose":
                echo.info(f"[NESTIPY] INFO [WEB] {text}")

        # Your existing code continues...
        if dev:
            web_args_list = shlex.split(web_args) if web_args else ["--vite"]
            web_args_list = _strip_backend_flags(web_args_list)
            web_app_dir = _extract_web_app_dir(web_args_list)
            web_out_dir = _extract_web_out_dir(web_args_list)
            if not _has_flag(web_args_list, "--vite"):
                web_args_list.append("--vite")
            if "--install" in web_args_list:
                show_web_install_log = True
                echo.info("[NESTIPY] INFO [WEB] Installing frontend dependencies...")
                install_args = [arg for arg in web_args_list if arg != "--install"]
                if not _has_flag(install_args, "--vite"):
                    install_args.append("--vite")
                install_proc = subprocess.Popen(
                    ["nestipy", "run", "web:install", *install_args],
                    cwd=str(module_file_path.parent),
                    env=os.environ.copy(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                if install_proc.stdout is not None:
                    for raw in iter(install_proc.stdout.readline, ""):
                        _handle_web_log(raw)
                    install_proc.stdout.close()
                install_code = install_proc.wait()
                if install_code != 0:
                    echo.error("[NESTIPY] ERROR [WEB] Frontend dependency install failed.")
                    return
                echo.success("[NESTIPY] INFO [WEB] Frontend dependencies installed.")
                web_args_list = [arg for arg in web_args_list if arg != "--install"]
            if not _has_flag(web_args_list, "--actions"):
                web_args_list.append("--actions")
            proxy_value = (
                _extract_flag_value(web_args_list, "--proxy")
                or os.getenv("NESTIPY_WEB_PROXY")
                or web_proxy
                or f"{scheme}://{host}:{selected_port}"
            )
            if not _has_flag(web_args_list, "--proxy") and not os.getenv("NESTIPY_WEB_PROXY"):
                web_args_list.extend(["--proxy", proxy_value])
            if ssr and not _has_flag(web_args_list, "--ssr"):
                web_args_list.append("--ssr")
            if ssr_entry and not _has_flag(web_args_list, "--ssr-entry"):
                web_args_list.extend(["--ssr-entry", ssr_entry])
            if not _has_flag(web_args_list, "--router-spec") and proxy_value:
                web_args_list.extend(["--router-spec", proxy_value.rstrip("/") + "/_router/spec"])
            echo.info(
                f"[NESTIPY] INFO [WEB] Starting dev server (nestipy run web:dev {' '.join(web_args_list)})"
            )
            web_host = (
                _extract_flag_value(web_args_list, "--host")
                or os.getenv("VITE_HOST")
                or "localhost"
            )
            web_port = (
                _extract_flag_value(web_args_list, "--port")
                or os.getenv("VITE_PORT")
                or "5173"
            )
            if web_host and web_port:
                web_dev_fallback_url = f"http://{web_host}:{web_port}"
            os.environ.setdefault("NESTIPY_ROUTER_SPEC", "1")
            env = os.environ.copy()
            env["NESTIPY_WEB_BACKEND"] = ""
            env["NESTIPY_WEB_BACKEND_CWD"] = ""
            env.setdefault("NESTIPY_ROUTER_SPEC", "1")
            actions_watch_paths: list[str] = []
            actions_watch_src = project_root / "src"
            if actions_watch_src.exists():
                actions_watch_paths.append(str(actions_watch_src))
            has_root_py = any(project_root.glob("*.py"))
            if has_root_py:
                actions_watch_paths.append(str(project_root))
            if not actions_watch_paths:
                actions_watch_paths.append(str(project_root))
            env.setdefault("NESTIPY_WEB_ACTIONS_WATCH", ",".join(actions_watch_paths))
            try:
                import pty

                master_fd, slave_fd = pty.openpty()
                web_process = subprocess.Popen(
                    ["nestipy", "run", "web:dev", *web_args_list],
                    cwd=str(module_file_path.parent),
                    env=env,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    text=False,
                )
                os.close(slave_fd)

                def _stream_web_fd(fd: int) -> None:
                    buffer = ""
                    try:
                        while True:
                            chunk = os.read(fd, 4096)
                            if not chunk:
                                break
                            buffer += chunk.decode("utf-8", errors="replace")
                            while "\n" in buffer or "\r" in buffer:
                                sep = "\n" if "\n" in buffer else "\r"
                                line, buffer = buffer.split(sep, 1)
                                _handle_web_log(line)
                    except OSError:
                        return
                    finally:
                        if buffer:
                            _handle_web_log(buffer)
                        try:
                            os.close(fd)
                        except Exception:
                            pass

                threading.Thread(target=_stream_web_fd, args=(master_fd,), daemon=True).start()
            except Exception:
                web_process = subprocess.Popen(
                    ["nestipy", "run", "web:dev", *web_args_list],
                    cwd=str(module_file_path.parent),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
                if web_process.stdout is not None:
                    threading.Thread(
                        target=_stream_web_logs, args=(web_process.stdout,), daemon=True
                    ).start()
                if web_process.stderr is not None:
                    threading.Thread(
                        target=_stream_web_logs, args=(web_process.stderr,), daemon=True
                    ).start()

            if web_dev_fallback_url:
                def _emit_web_dev_fallback() -> None:
                    nonlocal web_dev_reported
                    time.sleep(3)
                    if not web_dev_reported:
                        echo.info(
                            f"[NESTIPY] INFO [WEB] Dev server running on: {web_dev_fallback_url}"
                        )
                        web_dev_reported = True

                threading.Thread(target=_emit_web_dev_fallback, daemon=True).start()
            def _watch_web_process() -> None:
                code = web_process.wait()
                if code != 0:
                    echo.error(f"[NESTIPY] ERROR [WEB] Dev server exited (code={code}).")
                else:
                    echo.info("[NESTIPY] INFO [WEB] Dev server stopped.")
            threading.Thread(target=_watch_web_process, daemon=True).start()
            atexit.register(lambda: web_process and web_process.terminate())
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
    if cwd_root != project_root:
        if (cwd_root / "app").exists() and "app" not in reload_ignore_dirs_list:
            reload_ignore_dirs_list.append("app")
        if (cwd_root / "page").exists() and "page" not in reload_ignore_dirs_list:
            reload_ignore_dirs_list.append("page")
    if web:
        web_dir = project_root / "web"
        if web_dir.exists() and "web" not in reload_ignore_dirs_list:
            reload_ignore_dirs_list.append("web")
    if web_app_dir:
        web_app_path = (project_root / web_app_dir).resolve()
        if web_app_path.exists():
            web_app_name = web_app_path.name
            if web_app_name not in reload_ignore_dirs_list:
                reload_ignore_dirs_list.append(web_app_name)
    if web and "web_out_dir" in locals():
        web_out_path = (project_root / web_out_dir).resolve()
        if web_out_path.exists():
            web_out_name = web_out_path.name
            if web_out_name not in reload_ignore_dirs_list:
                reload_ignore_dirs_list.append(web_out_name)
    reload_paths_list = [_abs_path(p) for p in reload_paths]
    if dev and not reload_any and not reload_paths_list:
        reload_paths_list.append(str(project_root))

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
