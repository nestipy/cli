from __future__ import annotations

import copy
import contextlib
import inspect
import logging.config
import os
import re
import sys
import threading
import json
import os
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .config import LOGGING_CONFIG, PROD_LOGGER

HttpChoice = Literal["auto", "1", "2"]
LoopChoice = Literal["auto", "asyncio", "rloop", "uvloop"]


@dataclass(frozen=True)
class GranianStartConfig:
    app_path: str
    dev: bool
    host: str
    port: int
    workers: int
    ssl_keyfile: str | None
    ssl_cert_file: str | None
    loop: LoopChoice
    http: HttpChoice
    is_microservice: bool
    log_config_path: Path
    reload_any: bool
    reload_paths: list[str]
    reload_ignore_dirs: list[str]
    reload_ignore_patterns: list[str]
    reload_ignore_paths: list[str]
    reload_tick: int | None
    reload_ignore_worker_failure: bool


def select_port(port: int, is_microservice: bool) -> int:
    if is_microservice:
        return random.randint(5000, 7000)
    return port


def ensure_log_dir() -> Path:
    log_dir = Path(os.getcwd()) / "logs"
    log_dir.mkdir(exist_ok=True)
    (log_dir / "default.log").touch(exist_ok=True)
    (log_dir / "access.log").touch(exist_ok=True)
    return log_dir


def build_logging_config(dev: bool) -> dict[str, Any]:
    config = copy.deepcopy(LOGGING_CONFIG)
    if not dev:
        config["loggers"] = copy.deepcopy(PROD_LOGGER)
    return config


def configure_logging(config: dict[str, Any]) -> None:
    logging.config.dictConfig(config)


STATUS_COLORS = {
    "2xx": "32",
    "3xx": "36",
    "4xx": "33",
    "5xx": "31",
}


def _style_status(status: int) -> str:
    if 200 <= status < 300:
        return STATUS_COLORS["2xx"]
    if 300 <= status < 400:
        return STATUS_COLORS["3xx"]
    if 400 <= status < 500:
        return STATUS_COLORS["4xx"]
    if 500 <= status < 600:
        return STATUS_COLORS["5xx"]
    return "37"


def _extract_status_from_message(message: str) -> int | None:
    try:
        primary = re.search(r"\"[^\"]*\"\s+(\d{3})\b", message)
        if primary:
            value = int(primary.group(1))
            if 100 <= value <= 599:
                return value
        candidates = [
            int(match.group(1))
            for match in re.finditer(r"(?<!\d)(\d{3})(?!\d)", message)
            if 100 <= int(match.group(1)) <= 599
        ]
        if candidates:
            return candidates[-1]
    except Exception:
        return None
    return None


def _colorize_status_ansi(message: str) -> str:
    status = _extract_status_from_message(message)
    if status is None:
        return message
    color = _style_status(status)
    pattern = re.compile(rf"(?<!\d){status}(?!\d)")
    return pattern.sub(f"\x1b[{color}m{status}\x1b[32m", message, count=1)


def _rewrite_access_line(line: str) -> str | None:
    match = re.match(r"^\[(?P<ts>[^\]]+)\]\s+(?P<rest>.+)$", line)
    if not match:
        return None
    ts = match.group("ts")
    rest = match.group("rest")
    access = re.match(
        r'^(?P<client>.+?)\s+-\s+"(?P<req>[^"]+)"\s+(?P<status>\d{3})\s+(?P<duration>[0-9.]+)(?:\s*ms)?\s*$',
        rest,
    )
    if not access:
        return None
    client = access.group("client")
    req = access.group("req")
    status = access.group("status")
    duration = access.group("duration")
    return (
        f'[NESTIPY] INFO [{ts}] {client} - "{req}" {status} - {duration} ms'
    )


def rewrite_granian_line(line: str, use_color: bool = True) -> str:
    if line.startswith("[NESTIPY]"):
        if not use_color or "\x1b[" in line:
            return line
        colored = _colorize_status_ansi(line)
        return f"\x1b[32m{colored}\x1b[0m"
    access_line = _rewrite_access_line(line)
    if access_line:
        if not use_color:
            return access_line
        colored = _colorize_status_ansi(access_line)
        return f"\x1b[32m{colored}\x1b[0m"
    match = re.match(r"^\[(?P<level>[A-Z]+)\]\s*(?P<rest>.*)$", line)
    if not match:
        return line
    level = match.group("level")
    rest = match.group("rest")
    formatted = f"[NESTIPY] {level} {rest}".rstrip()
    if not use_color or "\x1b[" in line:
        return formatted
    colored = _colorize_status_ansi(formatted)
    return f"\x1b[32m{colored}\x1b[0m"


def _start_rewrite_thread(
    read_fd: int, write_fd: int, use_color: bool
) -> threading.Thread:
    def _reader() -> None:
        buffer = ""
        while True:
            try:
                chunk = os.read(read_fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                os.write(
                    write_fd,
                    (rewrite_granian_line(line, use_color=use_color) + "\n").encode(
                        "utf-8"
                    ),
                )
        if buffer:
            os.write(
                write_fd,
                rewrite_granian_line(buffer, use_color=use_color).encode("utf-8"),
            )

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    return thread


@contextlib.contextmanager
def granian_log_prefixer():
    stdout_fd = sys.stdout.fileno()
    stderr_fd = sys.stderr.fileno()
    use_color = (
        os.isatty(stdout_fd) and os.getenv("NO_COLOR") is None
    )
    orig_stdout_fd = os.dup(stdout_fd)
    orig_stderr_fd = os.dup(stderr_fd)
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()

    os.dup2(stdout_w, stdout_fd)
    os.dup2(stderr_w, stderr_fd)
    os.close(stdout_w)
    os.close(stderr_w)

    stdout_thread = _start_rewrite_thread(stdout_r, orig_stdout_fd, use_color)
    stderr_thread = _start_rewrite_thread(stderr_r, orig_stderr_fd, use_color)

    try:
        yield
    finally:
        os.dup2(orig_stdout_fd, stdout_fd)
        os.dup2(orig_stderr_fd, stderr_fd)
        os.close(orig_stdout_fd)
        os.close(orig_stderr_fd)
        os.close(stdout_r)
        os.close(stderr_r)
        stdout_thread.join(timeout=0.2)
        stderr_thread.join(timeout=0.2)


def write_logging_config(config: dict[str, Any]) -> Path:
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as handle:
        json.dump(config, handle)
        return Path(handle.name)


PY_RELOAD_IGNORE_PATTERNS = [
    r".*\.(?!(py|pyi|pyx|pyd)$)[^.]+$",
]


def build_granian_options(cfg: GranianStartConfig) -> dict[str, Any]:
    reload_ignore_patterns = list(cfg.reload_ignore_patterns)
    if cfg.dev and not cfg.reload_any:
        reload_ignore_patterns = PY_RELOAD_IGNORE_PATTERNS + reload_ignore_patterns
    reload_ignore_patterns = reload_ignore_patterns or None
    reload_paths = (
        [Path(p).resolve() for p in cfg.reload_paths] if cfg.reload_paths else None
    )
    reload_ignore_dirs = cfg.reload_ignore_dirs or None
    reload_ignore_paths = (
        [Path(p).resolve() for p in cfg.reload_ignore_paths]
        if cfg.reload_ignore_paths
        else None
    )
    access_enabled = not cfg.is_microservice
    print("[NESTIPY] INFO [RELOAD] paths:", reload_paths)
    print("[NESTIPY] INFO [RELOAD] ignore_paths:", reload_ignore_paths)
    print("[NESTIPY] INFO [RELOAD] ignore_dirs:", reload_ignore_dirs)
    print("[NESTIPY] INFO [RELOAD] ignore_patterns:", reload_ignore_patterns)
    options: dict[str, Any] = {
        "interface": "asgi",
        "host": cfg.host,
        "port": cfg.port,
        "workers": cfg.workers,
        "loop": cfg.loop,
        "http": cfg.http,
        "log_config": str(cfg.log_config_path),
        "reload_paths": reload_paths,
        "reload_ignore_dirs": reload_ignore_dirs,
        "reload_ignore_patterns": reload_ignore_patterns,
        "reload_ignore_paths": reload_ignore_paths,
        "reload_tick": cfg.reload_tick,
        "reload_ignore_worker_failure": cfg.reload_ignore_worker_failure,
        "log_access_enabled": access_enabled,
        "log_access": access_enabled,
        "log_level": "critical" if cfg.is_microservice else None,
        "access_log": access_enabled,
        "no_access_log": not access_enabled,
        "ssl_keyfile": cfg.ssl_keyfile,
        "ssl_certfile": cfg.ssl_cert_file,
        "ssl_certificate": cfg.ssl_cert_file,
        "reload": cfg.dev,
    }
    return {key: value for key, value in options.items() if value is not None}


def resolve_granian_init_args(
    cfg: GranianStartConfig, signature: inspect.Signature
) -> tuple[list[Any], dict[str, Any]]:
    params = signature.parameters
    args: list[Any] = []
    kwargs: dict[str, Any] = {}

    for key in ("app", "app_path", "target"):
        if key in params:
            param = params[key]
            if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                args.append(cfg.app_path)
            else:
                kwargs[key] = cfg.app_path
            break
    else:
        for param in params.values():
            if param.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ) and param.default is inspect.Parameter.empty:
                args.append(cfg.app_path)
                break

    options = build_granian_options(cfg)
    for key, value in options.items():
        if key in params:
            kwargs[key] = value

    return args, kwargs


def create_granian_instance(cfg: GranianStartConfig):
    from granian import Granian

    args, kwargs = resolve_granian_init_args(cfg, inspect.signature(Granian))
    return Granian(*args, **kwargs)
