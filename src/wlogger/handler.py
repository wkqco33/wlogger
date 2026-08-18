from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from .formatter import ColorFormatter, JsonFormatter


class _WloggerStreamHandler(logging.StreamHandler[TextIO]):
    pass


class _WloggerRotatingFileHandler(logging.handlers.RotatingFileHandler):
    pass


def _supports_color(stream: TextIO) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(callable(isatty) and isatty())


def make_console_handler(
    level: int = logging.DEBUG, *, stream: TextIO | None = None
) -> logging.StreamHandler[TextIO]:
    # 진단용 로그가 애플리케이션의 stdout 출력과 섞이지 않도록 stderr 기본 사용
    target = stream if stream is not None else sys.stderr
    handler = _WloggerStreamHandler(target)
    handler.setLevel(level)
    handler.setFormatter(ColorFormatter(use_color=_supports_color(target)))
    return handler


def make_file_handler(
    path: str,
    level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    *,
    json_default: Callable[[object], object] | None = str,
) -> logging.handlers.RotatingFileHandler:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = _WloggerRotatingFileHandler(
        str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(JsonFormatter(json_default=json_default))
    return handler


def is_wlogger_handler(handler: logging.Handler) -> bool:
    return isinstance(handler, (_WloggerStreamHandler, _WloggerRotatingFileHandler))
