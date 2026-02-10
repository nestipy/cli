from __future__ import annotations

import copy
import contextlib
import inspect
import logging.config
import re
import sys
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


def rewrite_granian_line(line: str) -> str:
    if line.startswith("[NESTIPY]"):
        return line
    match = re.match(r"^\[(?P<level>[A-Z]+)\]\s*(?P<rest>.*)$", line)
    if not match:
        return line
    level = match.group("level")
    rest = match.group("rest")
    if rest:
        return f"[NESTIPY] {level} {rest}"
    return f"[NESTIPY] {level}"


class _PrefixedStream:
    def __init__(self, stream):
        self._stream = stream
        self._buffer = ""

    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode(getattr(self._stream, "encoding", None) or "utf-8")
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._stream.write(rewrite_granian_line(line) + "\n")

    def flush(self):
        if self._buffer:
            self._stream.write(rewrite_granian_line(self._buffer))
            self._buffer = ""
        self._stream.flush()

    def isatty(self):
        return self._stream.isatty()

    def fileno(self):
        return self._stream.fileno()

    @property
    def encoding(self):
        return getattr(self._stream, "encoding", "utf-8")

    @property
    def errors(self):
        return getattr(self._stream, "errors", "strict")


@contextlib.contextmanager
def granian_log_prefixer():
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = _PrefixedStream(original_stdout)
    sys.stderr = _PrefixedStream(original_stderr)
    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr


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
