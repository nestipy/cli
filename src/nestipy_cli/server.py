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


LEVEL_COLORS = {
    "DEBUG": "36",
    "INFO": "32",
    "WARNING": "33",
    "WARN": "33",
    "ERROR": "31",
    "CRITICAL": "1;31",
}


def _colorize_level(level: str) -> str:
    color = LEVEL_COLORS.get(level, "37")
    return f"\x1b[{color}m{level}\x1b[0m"


def rewrite_granian_line(line: str, use_color: bool = True) -> str:
    if line.startswith("[NESTIPY]"):
        return line
    match = re.match(r"^\[(?P<level>[A-Z]+)\]\s*(?P<rest>.*)$", line)
    if not match:
        return line
    level = match.group("level")
    rest = match.group("rest")
    colored_level = (
        _colorize_level(level)
        if use_color and "\x1b[" not in line
        else level
    )
    if rest:
        return f"[NESTIPY] {colored_level} {rest}"
    return f"[NESTIPY] {colored_level}"


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


def build_granian_options(cfg: GranianStartConfig) -> dict[str, Any]:
    options: dict[str, Any] = {
        "interface": "asgi",
        "host": cfg.host,
        "port": cfg.port,
        "workers": cfg.workers,
        "loop": cfg.loop,
        "http": cfg.http,
        "log_config": str(cfg.log_config_path),
        "log_level": "critical" if cfg.is_microservice else None,
        "access_log": not cfg.is_microservice,
        "no_access_log": cfg.is_microservice,
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
